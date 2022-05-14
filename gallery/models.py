from django.db import models

from django_extensions.db.models import TimeStampedModel



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

    class Meta:
        verbose_name_plural = "Categories"

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

    def get_next_id(self, curr_id):
        """Find the next Image in this album, based on `album_order`."""

        try:
            _ret = (
                Image.objects.filter(album_order__gte=self.album_order)
                .exclude(id=self.id)
                .order_by("album_order", "id")
                .first()
            )
        except Image.DoesNotExist:
            _ret = None
        return _ret

    def get_previous_id(self, curr_id):
        """Find the previous Image in this album, based on `album_order`."""

        try:
            _ret = (
                Image.objects.filter(album_order__lte=self.album_order)
                .exclude(id=self.id)
                .order_by("-album_order", "-id")
                .first()
            )
        except Image.DoesNotExist:
            _ret = None
        return _ret

    def __str__(self) -> str:
        return str(self.flickr_id)
