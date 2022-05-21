from dataclasses import asdict
from itertools import cycle

from django.shortcuts import get_object_or_404, render

from gallery.models import Album, Image, SimplePage
from gallery.utils import get_api_image_data, get_prev_next_ids


def home(request):
    """Show about text and array of album thumbnails"""
    ctx = {"albums": Album.objects.all().order_by("order")}
    return render(request, "home.html", context=ctx)


def album(request, slug: str):
    """Show about text and array of image thumbnails in this album"""
    album = Album.objects.get(slug=slug)
    images = Image.objects.filter(album=album).order_by("album_order")

    # For Responsive Image Grid, we will always have four columns, but need to arrange the image set
    # in rows, respecting album image order left to right. So we set up four lists - one for each column.
    # Then iterate through images and drop them in columns, in order. On the resulting page, we render
    # thumbnails in columns, not rows.
    columns = [[], [], [], []]
    cycled_columns = cycle(columns)
    for image in images:
        next(cycled_columns).append(image)

    ctx = {"album": album, "columns": columns}
    return render(request, "album.html", context=ctx)


def image(request, album_slug: str, flickr_id: int):
    """Show image detail, with a combination of locally stored image data
    and data retrieved from Flickr API."""

    # No crash protection on .get() but this image should never be called
    # without a valid flickr_id passed in.
    img = get_object_or_404(Image, flickr_id=flickr_id)
    flickr = asdict(get_api_image_data(flickr_id))
    prev_next_ids = get_prev_next_ids(img)

    ctx = {
        "img": img,
        "flickr": flickr,
        "prev_next_ids": prev_next_ids,
    }

    return render(request, "image.html", context=ctx)


def about(request):
    """Just render About template"""
    page = get_object_or_404(SimplePage, title="About")
    return render(request, "about.html", {"page": page})
