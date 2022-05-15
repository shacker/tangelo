from django.shortcuts import render, redirect
from gallery.models import Category, Image
from gallery.utils import get_api_image_data
from dataclasses import asdict
from django.views.decorators.cache import cache_page
from django.core.management import call_command
from django.conf import settings

@cache_page(settings.CACHE_TTL)
def home(request):
    """Show about text and array of category thumbnails"""
    ctx = {"categories": Category.objects.all()}
    return render(request, "home.html", context=ctx)


@cache_page(settings.CACHE_TTL)
def category(request, slug: str):
    """Show about text and array of image thumbnails in this category"""
    category = Category.objects.get(slug=slug)
    ctx = {
        "images": Image.objects.filter(
            categories__in=[
                category,
            ]
        ).order_by("album_order")
    }
    return render(request, "category.html", context=ctx)


@cache_page(settings.CACHE_TTL)
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
