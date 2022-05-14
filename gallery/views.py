from django.shortcuts import render
from gallery.models import Category, Image
from gallery.utils import get_api_image_data
from dataclasses import asdict


def home(request):
    """Show about text and array of category thumbnails"""
    ctx = {"categories": Category.objects.all()}
    return render(request, "home.html", context=ctx)


def category(request, slug: str):
    """Show about text and array of image thumbnails in this category"""
    category = Category.objects.get(slug=slug)
    ctx = {
        "images": Image.objects.filter(
            categories__in=[
                category,
            ]
        )
    }
    return render(request, "category.html", context=ctx)


def image(request, flickr_id: int):
    """Show image detail"""

    image_data = get_api_image_data(flickr_id)

    return render(request, "image.html", context=asdict(image_data))
