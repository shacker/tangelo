from django.db import models

from django_extensions.db.models import TimeStampedModel


# class HomePage(TimeStampedModel):
#     """
#     Stores settings related to defined Greenhouse services.
#     """

#     models.TextField(help_text="Intro text to be displayed")


class CategoryPage(TimeStampedModel):
    """
    Stores settings related to defined Greenhouse services.
    """

    title = models.CharField(max_length=120, help_text="Unique name for this service.", unique=True)
    slug = models.CharField(max_length=16, help_text="Slugified version of this category title.", unique=True)
    about = models.TextField(help_text="Some info about this category")

    def __str__(self) -> str:
        return self.title

class ImagePage(TimeStampedModel):
    """
    Put images in categories
    """

    flickr_id = models.IntegerField(help_text="Unique ID of a Flickr image")
    title = models.CharField(max_length=120, help_text="Auto-copied from Flickr title, can be overridden", blank=True)
    # description = models.CharField(max_length=120, help_text="Auto-copied from Flickr title, can be overridden", blank=True)
    categories = models.ManyToManyField(CategoryPage, help_text="An image can exist in many categories at once.")

    def __str__(self) -> str:
        return str(self.flickr_id)
