from django.shortcuts import render, redirect
from gallery.models import Category, Image
from gallery.utils import get_api_image_data
from dataclasses import asdict
from django.core.management import call_command
from itertools import cycle


def home(request):
    """Show about text and array of category thumbnails"""
    ctx = {"categories": Category.objects.all().order_by("order")}
    return render(request, "home.html", context=ctx)


def category(request, slug: str):
    """Show about text and array of image thumbnails in this category"""
    category = Category.objects.get(slug=slug)
    images = Image.objects.filter(
            categories__in=[
                category,
            ]
        ).order_by("album_order")

    # For Responsive Image Grid, we will always have four columns, but need to arrange the image set
    # in rows, respecting album image order left to right. So we set up four lists - one for each column.
    # Then iterate through images and drop them in columns, in order.
    columns = [[], [], [], []]
    cycled_columns = cycle(columns)
    for image in images:
        next(cycled_columns).append(image)

    ctx = {
        "columns": columns
    }
    return render(request, "category.html", context=ctx)


def image(request, flickr_id: int):
    """Show image detail, with a combination of locally stored image data
    and data retrieved from Flickr API."""

    # No crash protection on .get() but this image should never be called
    # without a valid flickr_id passed in.
    img = Image.objects.get(flickr_id=flickr_id)
    flickr = asdict(get_api_image_data(flickr_id))

    ctx = {
        "img": img,
        "flickr": flickr,
        "next_id": img.get_next_id(flickr_id),
        "previous_id": img.get_previous_id(flickr_id),
    }

    return render(request, "image.html", context=ctx)


def clear_cache(request):
    """ Clear all caches. Superuser-only (but harmless) """
    call_command("clear_cache")
    return redirect("home")


def about(request):
    """ Just render about template """
    return render(request, "about.html")
