import logging
import math
import random
import re

import flickrapi
from dateutil import parser
from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import RegexValidator
from django.db import models
from django_extensions.db.models import TimeStampedModel

log = logging.getLogger(__name__)


class Album(TimeStampedModel):

    title = models.CharField(
        max_length=120, help_text="Descriptive name for this album.", unique=True
    )

    # Not doing auto-slug by preference
    slug = models.CharField(
        max_length=16,
        help_text="Slugified version of this album title for use in URLs.",
        unique=True,
    )
    about = models.TextField(help_text="Optional additional information this album", blank=True)

    order = models.IntegerField(
        help_text="Controls ordering of album thumbnails on homepage", blank=True, null=True
    )

    cat_thumb = models.ForeignKey(
        "gallery.Image",
        verbose_name=("Album Thumbnail"),
        related_name="album_thumb",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Each album should be associated with one of the images in that album, to be used in web layouts.",
    )

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class Image(TimeStampedModel):
    """
    When entering a Flickr ID, in the save() method, retrieve image metadata
    and save to the model. Subsequent changes override API data.
    """

    flickr_id = models.BigIntegerField(help_text="Unique Flickr ID for each image", unique=True)

    image_api_data = models.JSONField(
        encoder=DjangoJSONEncoder,
        default=dict,
        help_text="Stores full image detail response from Flickr getInfo API.",
        blank=True,
    )

    title = models.CharField(
        max_length=120,
        help_text="Title auto-copied from Flickr title, can be overridden",
        blank=True,
    )

    taken = models.DateTimeField(
        auto_now=False,
        auto_now_add=False,
        blank=True,
        null=True,
        help_text="Datetime when image was captured, as reported by Flickr API.",
    )

    albums = models.ManyToManyField(Album, blank=True, related_name="images")

    # album_order is ambiguous when image is in multiple albums, but letting that slide...
    album_order = models.IntegerField(
        help_text="Controls ordering of image within albums, and next/prev links.",
        blank=True,  # but not null=True!
        default=0,
        db_index=True,  # required by django-sortable
    )

    # ### START METHODS ###

    def get_api_image_data(self):
        """
        Use Flickr's getInfo() API to get metadata about an image by ID.
        https://www.flickr.com/services/api/flickr.photos.getInfo.html

        Returns
            Raw API response data
        """

        flickr = flickrapi.FlickrAPI(
            settings.FLICKR_API_KEY, settings.FLICKR_API_SECRET, format="parsed-json"
        )
        response = flickr.photos.getInfo(photo_id=self.flickr_id)
        return response

    def refetch(self):
        """We normally don't overwrite our own db entries after the first
        save. But if this is called, we DO reach out to Flickr API again
        to grab all data and repopulate our own db.
        """
        response = self.get_api_image_data()

        # Store API result in our own db
        self.image_api_data = response

        # Store a copy of the date so it's a real date we can sort on
        try:
            self.taken = parser.parse(response["photo"]["dates"]["taken"])
        except:
            log.info(f"Could not store date taken for image {self.flickr_id}")

        self.title = response["photo"]["title"]["_content"]

        # Also set the album_order to the next highest - can be adjusted later
        # Don't crash when saving the very first image.
        if Image.objects.exists():
            last_img_id = Image.objects.order_by("album_order").last().album_order
            self.album_order = last_img_id + 1
        else:
            self.album_order = 1

    def flush_cache(self):
        """Empty image cache for this image only.
        No return value."""

        key = make_template_fragment_key("flickr_full", [self.flickr_id])
        cache.delete(key)
        key = make_template_fragment_key("flickr_thumb", [self.flickr_id])
        cache.delete(key)

    def get_page_data(self):
        """Stored API data is a bit hairy. Extract just what we need to provide
        a simplified dict for use in templates.
        """
        raw = self.image_api_data["photo"]
        data = {
            "title": raw["title"]["_content"],
            "description": raw["description"]["_content"],
            "flickr_page_url": raw["urls"]["url"][0]["_content"],
            "flickr_embed_url": self.get_embed_url(),
        }

        return data

    def get_embed_url(self, size: str = settings.FLICKR_IMAGE_SIZE):
        """Compute the embed_url from stored API data combined with
        a sizing argument. Works for both full-size and thumbnails
        (any size, really).

        Args:
            size: Optional suffix mapping, per URL docs:
            https://www.flickr.com/services/api/misc.urls.html
            Defaults to "h" (1600 on the long side)

        Returns:
            A fully formed URL suitable for use in <img src="xxx">

        """
        photo = self.image_api_data["photo"]
        server = photo["server"]

        # Per docs, use 'secret' for images below 1600px,
        # 'originalsecret' for images 1600 or larger.
        originalsecret = photo["originalsecret"]
        embed_url = (
            f"https://live.staticflickr.com/{server}/{self.flickr_id}_{originalsecret}_{size}.jpg"
        )

        return embed_url

    def get_prev_next_ids(self):
        """Finds prev/next image IDs in the first album this image belongs to.

        Returns: {"prev": prev_id, "next": next_id} — either can be None.
        """

        next_id = None
        prev_id = None

        album = self.albums.first()
        if album is None:
            return {"prev": None, "next": None}

        qs = Image.objects.filter(albums=album).exclude(flickr_id=self.flickr_id)

        next_id_qs = qs.filter(taken__lt=self.taken).order_by("-taken")
        if next_id_qs.exists():
            next_id = next_id_qs.first().flickr_id

        prev_id_qs = qs.filter(taken__gt=self.taken).order_by("taken")
        if prev_id_qs.exists():
            prev_id = prev_id_qs.first().flickr_id

        return {"prev": prev_id, "next": next_id}

    def save(self, *args, **kwargs):
        """On first save of an image, auto-populate title and date
        from API, store the full response, and compute next album_order ID."""

        if not self.id:
            self.refetch()

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.title} ({str(self.flickr_id)})"

    class Meta:
        ordering = ["album_order"]


class SimplePage(TimeStampedModel):
    """
    Basic content page with a Markdown text field (mostly for "About").
    """

    title = models.CharField(
        max_length=120,
        help_text="Title for this page",
    )

    slug = models.CharField(
        max_length=120,
        help_text="Manually slugified version of the title",
    )

    body = models.TextField(help_text="General purpose text area")

    def __str__(self) -> str:
        return self.title


# ### FRAME INVENTORY ###
# Tracks handmade/vintage frames married with prints. Mirrors the "Frames"
# spreadsheet (Prints + Old metal prints sheets). Lookup models below hold
# the option lists for Price, State, Location, and FrameType.


DEFAULT_TAG_COLOR = "#e8eaed"


def tag_color_field():
    """Background color for this option's tag in the /frames grid."""
    return models.CharField(
        max_length=7,
        default=DEFAULT_TAG_COLOR,
        validators=[RegexValidator(r"^#[0-9a-fA-F]{6}$", "Use a hex color like #b7e1cd.")],
        help_text="Tag color in the frames grid.",
    )


class Price(TimeStampedModel):
    """A price point offered for framed prints. "Unset" in the spreadsheet
    is represented by a null Frame.price, not a row here."""

    amount = models.PositiveIntegerField(unique=True, help_text="Price in whole US dollars.")
    color = tag_color_field()

    class Meta:
        ordering = ["amount"]

    def __str__(self) -> str:
        return f"${self.amount}"


class FrameState(TimeStampedModel):
    """Workflow state for a frame (Done, Needs mat, Redo, etc.).
    A frame can hold several states at once."""

    name = models.CharField(max_length=60, unique=True)
    color = tag_color_field()
    order = models.IntegerField(
        default=0, help_text="Controls display order of states in admin lists."
    )

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "frame state"

    def __str__(self) -> str:
        return self.name


class FrameType(TimeStampedModel):
    """Kind of frame: Metal, Handmade, Vintage, Paper, etc."""

    name = models.CharField(max_length=60, unique=True)
    color = tag_color_field()

    class Meta:
        ordering = ["name"]
        verbose_name = "frame type"

    def __str__(self) -> str:
        return self.name


class AspectRatio(TimeStampedModel):
    """Standard print aspect ratio (1:1, 5:4, 3:2, ...), long side : short side."""

    name = models.CharField(max_length=20, unique=True, help_text='e.g. "3:2".')
    ratio = models.DecimalField(
        max_digits=6, decimal_places=3, help_text="Long side / short side, e.g. 1.5 for 3:2."
    )
    color = tag_color_field()

    class Meta:
        ordering = ["ratio"]
        verbose_name = "aspect ratio"

    def __str__(self) -> str:
        return self.name


ASPECT_TEXT = re.compile(r"(\d+(?:\.\d+)?)\s*[:x\u00d7/]\s*(\d+(?:\.\d+)?)")


def parse_aspect(text: str):
    """Ratio (long/short, >= 1) from text like "5:4", "1.37:1", "4:5 vertical"; else None."""
    m = ASPECT_TEXT.search(text or "")
    if not m:
        return None
    a, b = float(m.group(1)), float(m.group(2))
    if not a or not b:
        return None
    return max(a, b) / min(a, b)


def closest_aspect_ratio(value):
    """The AspectRatio closest to a numeric ratio (compared on a log scale), or None."""
    if not value:
        return None
    return min(
        AspectRatio.objects.all(), key=lambda r: abs(math.log(value / float(r.ratio))), default=None
    )


def nearest_aspect_ratio(text: str):
    """The AspectRatio closest to the ratio in text like "5:4" or "1.37:1", or None."""
    return closest_aspect_ratio(parse_aspect(text))


# A dimension: decimal, whole + fraction ("14 7/16"), or bare fraction.
_DIM_NUM = r"\d+(?:\.\d+)?(?:\s+\d+/\d+)?|\d+/\d+"
DIMENSIONS_TEXT = re.compile(rf"({_DIM_NUM})\s*(?:\"|in)?\s*[xX\u00d7]\s*({_DIM_NUM})")


def _dim_value(text: str) -> float:
    total = 0.0
    for part in text.split():
        if "/" in part:
            num, den = part.split("/")
            total += float(num) / float(den) if float(den) else 0.0
        else:
            total += float(part)
    return total


def parse_dimensions(text: str):
    """Ratio (long/short) from dimensions like "14 7/16 x 9" or "12x 8"; else None."""
    m = DIMENSIONS_TEXT.search(text or "")
    if not m:
        return None
    a, b = _dim_value(m.group(1)), _dim_value(m.group(2))
    return max(a, b) / min(a, b) if a and b else None


def aspect_from_dimensions(image_dimension: str, rabbet_size: str):
    """Aspect from the image dimension, falling back to the rabbet size."""
    value = parse_dimensions(image_dimension) or parse_dimensions(rabbet_size)
    return closest_aspect_ratio(value)


class Location(TimeStampedModel):
    """Where a framed print currently lives (Home, a venue, gifted, etc.)."""

    name = models.CharField(max_length=120, unique=True)
    color = tag_color_field()

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


def default_location():
    """Default Frame.location to "Home", if that Location exists."""
    loc = Location.objects.filter(name="Home").first()
    return loc.pk if loc else None


def generate_photo_id() -> int:
    """Return a random five-digit Photo ID not already used by any Frame.
    Used as the field default, so the admin "add" form is pre-filled."""
    used = set(Frame.objects.values_list("photo_id", flat=True))
    available = [n for n in range(10000, 100000) if n not in used]
    if not available:
        raise ValueError("All five-digit Photo IDs are in use.")
    return random.choice(available)


class Frame(TimeStampedModel):
    """A handmade or vintage frame, usually married with one of my prints."""

    title = models.CharField(max_length=200, blank=True)
    lr_id = models.CharField(
        "LR ID", max_length=100, blank=True, help_text="Lightroom identifier/filename."
    )
    price = models.ForeignKey(
        Price,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="frames",
        help_text="Leave blank if price is unset.",
    )
    image = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="frames",
        verbose_name="Flickr Image",
        help_text="Gallery image this frame's print was made from. Search by title or Flickr ID.",
    )
    photo_id = models.PositiveIntegerField(
        "Photo ID",
        unique=True,
        default=generate_photo_id,
        help_text="Unused five-digit ID, auto-generated for new frames.",
    )
    frame = models.CharField(max_length=200, blank=True, help_text="Frame description.")
    frame_type = models.ForeignKey(
        FrameType,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="frames",
    )
    states = models.ManyToManyField(FrameState, blank=True, related_name="frames")
    image_dimension = models.CharField(
        max_length=50, blank=True, help_text='Free text, e.g. "18 x 12".'
    )
    rabbet_size = models.CharField(
        max_length=50, blank=True, help_text='Free text, e.g. "14 7/16 x 9".'
    )
    aspect = models.ForeignKey(
        AspectRatio,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="frames",
        help_text="Computed from Image dimension (or Rabbet size) unless set by hand.",
    )
    aspect_manual = models.BooleanField(
        "Aspect set by hand",
        default=False,
        help_text="Checked: keep the chosen aspect. Unchecked: recompute it from the dimensions.",
    )
    notes = models.TextField(blank=True)
    print_cost = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        default=default_location,
        blank=True,
        null=True,
        related_name="frames",
    )
    print_order = models.CharField(
        max_length=100, blank=True, help_text='Vendor + order number, e.g. "Luma 10001872570".'
    )

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title or f"Untitled ({self.lr_id or self.photo_id or self.pk})"

    def save(self, *args, **kwargs):
        """Unless the aspect was set by hand, keep it in step with the dimensions."""
        if not self.aspect_manual:
            self.aspect = aspect_from_dimensions(self.image_dimension, self.rabbet_size)
            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"aspect"}
        super().save(*args, **kwargs)
