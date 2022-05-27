from dataclasses import asdict

from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db import models
from django_extensions.db.models import TimeStampedModel

from gallery.utils import get_api_image_data


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

    def get_thumbnail(self):
        """Using the `cat_thumb` field on this album, get thumbnail image for this album via Flickr API."""

        flickr_data = None
        if self.cat_thumb:
            flickr_data = asdict(
                get_api_image_data(self.cat_thumb.flickr_id, size=settings.FLICKR_THUMBNAIL_SIZE)
            )

        return flickr_data

    def __str__(self) -> str:
        return self.title


class Image(TimeStampedModel):
    """
    When entering a Flickr ID, in the save() method, retrieve image metadata
    and save to the model. Subsequent changes override API data.
    """

    flickr_id = models.BigIntegerField(help_text="Unique Flickr ID for each image", unique=True)
    title = models.CharField(
        max_length=120,
        help_text="Title auto-copied from Flickr title, can be overridden",
        blank=True,
    )
    description = models.TextField(
        help_text="Description auto-copied from Flickr description, can be overridden", blank=True
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

    def get_thumbnail(self):
        """Get a thumbnail version of this image via Flickr API."""

        flickr_data = asdict(
            get_api_image_data(self.flickr_id, size=settings.FLICKR_THUMBNAIL_SIZE)
        )
        return flickr_data

    def flush_cache(self):
        """ Empty image cache for this image only.
        No return value. """

        key = make_template_fragment_key("flickr_full", [self.flickr_id])
        cache.delete(key)
        key = make_template_fragment_key("flickr_thumb", [self.flickr_id])
        cache.delete(key)

    def refetch(self):
        """ We normally don't overwrite our own db entries after the first
        save. But if this is called, we DO reach out to Flickr API again
        to grab all data and repopulate our own db.
        """
        flickr = get_api_image_data(flickr_id=self.flickr_id)
        self.title = flickr.title
        self.description = flickr.description
        self.taken = flickr.taken

        # Also set the album_order to the next highest - can be adjusted later
        # Don't crash when saving the very first image.
        if Image.objects.exists():
            last_img_id = Image.objects.order_by("album_order").last().album_order
            self.album_order = last_img_id + 1
        else:
            self.album_order = 1

        self.save()

    def save(self, *args, **kwargs):
        """On first save of an image, auto-populate title and description
        via API, and compute next album_order ID."""

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
