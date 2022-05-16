from django.db import models
from django.conf import settings
from django_extensions.db.models import TimeStampedModel
from gallery.utils import get_api_image_data
from dataclasses import asdict


class Category(TimeStampedModel):

    title = models.CharField(
        max_length=120, help_text="Descriptive name for this category.", unique=True
    )

    # Not doing auto-slug by preference
    slug = models.CharField(
        max_length=16,
        help_text="Slugified version of this category title for use in URLs.",
        unique=True,
    )
    about = models.TextField(help_text="Optional additional information this category", blank=True)

    cat_thumb = models.ForeignKey(
        "gallery.Image",
        verbose_name=("Category Thumbnail"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Each category should be associated with one of the images in that category, to be used in web layouts.",
    )

    class Meta:
        verbose_name_plural = "Categories"

    def get_thumbnail(self):
        """Using the `cat_thumb` field on this category, get thumbnail image for this cat via Flickr API."""

        flickr_data = None
        if self.cat_thumb:
            flickr_data = asdict(get_api_image_data(self.cat_thumb.flickr_id, size=settings.FLICKR_THUMBNAIL_SIZE))

        return flickr_data

    def __str__(self) -> str:
        return self.title


class Image(TimeStampedModel):
    """
    TODO: Undecided - we do need Title here for reference to it in Admin lists, but really we can get
    title and description from Flickr in real-time. Keep description at all?
    """

    flickr_id = models.BigIntegerField(help_text="Unique Flickr ID for each image")
    title = models.CharField(
        max_length=120,
        help_text="Title auto-copied from Flickr title, can be overridden",
        blank=True,
    )
    description = models.TextField(
        help_text="Description auto-copied from Flickr description, can be overridden", blank=True
    )
    categories = models.ManyToManyField(
        Category, help_text="An image can exist in many categories at once."
    )

    # Since an image can belong to more than one category, album_order is ambiguous when
    # image is in multiple categories, but letting that slide for now...
    album_order = models.IntegerField(
        help_text="Controls ordering of image within albums, and next/prev links."
    )

    def get_thumbnail(self):
        """Get a thumbnail version of this image via Flickr API."""

        flickr_data = asdict(get_api_image_data(self.flickr_id, size=settings.FLICKR_THUMBNAIL_SIZE))
        return flickr_data

    def get_next_id(self, curr_id):
        """Find the next Image in this album, based on `album_order`."""

        try:
            _ret = (
                Image.objects.filter(album_order__gte=self.album_order)
                .exclude(id=self.id)
                .order_by("album_order", "id")
                .first().flickr_id
            )
        except (Image.DoesNotExist, AttributeError):
            _ret = None
        return _ret

    def get_previous_id(self, curr_id):
        """Find the previous Image in this album, based on `album_order`."""

        try:
            _ret = (
                Image.objects.filter(album_order__lte=self.album_order)
                .exclude(id=self.id)
                .order_by("-album_order", "-id")
                .first().flickr_id
            )
        except (Image.DoesNotExist, AttributeError):
            _ret = None
        return _ret

    def save(self, *args, **kwargs):
        """ On first save of an image, auto-populate title and description
        """

        if not self.id:
            flickr = get_api_image_data(flickr_id=self.flickr_id)
            self.title = flickr.title
            self.description = flickr.description

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.title} ({str(self.flickr_id)})"
