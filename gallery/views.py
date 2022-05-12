from django.shortcuts import render
from gallery.models import CategoryPage, ImagePage


def home(request):
    """Show about text and array of category thumbnails"""
    ctx = {"categories": CategoryPage.objects.all()}
    return render(request, "home.html", context=ctx)


def category(request, slug: str):
    """Show about text and array of image thumbnails in this category"""
    category = CategoryPage.objects.get(slug=slug)
    ctx = {
        "images": ImagePage.objects.filter(
            categories__in=[
                category,
            ]
        )
    }
    return render(request, "category.html", context=ctx)


def image(request, flickr_id: int):
    """Show image detail"""

    # TODO: Crash protection
    image = ImagePage.objects.get(flickr_id=flickr_id)
    ctx = {"image": image}
    return render(request, "image.html", context=ctx)
