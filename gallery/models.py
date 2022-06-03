import logging

import flickrapi
from dateutil import parser
from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.serializers.json import DjangoJSONEncoder
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

    album = models.ForeignKey(Album, on_delete=models.CASCADE)

    # Since an image can belong to more than one category, album_order is ambiguous when
    # image is in multiple categories, but letting that slide for now...
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
        """Given an Image instance, finds the previous and next
            Image IDs in an album, based on `taken` (date taken).
            n.b. Originally written to order by manual `album_order`
            but decided I preferred simple auto date ordering to keep things fresh.

        Returns:
            {"prev": prev_id, "next": next_id}
            Either of these can be None if there is no previous or next.
        """

        from gallery.models import Image

        next_id = None
        prev_id = None

        # Start with a queryset of all images in this image's album, except self
        qs = Image.objects.filter(album=self.album).exclude(flickr_id=self.flickr_id)

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
