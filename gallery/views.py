from itertools import cycle

from django.conf import settings
from django.core.mail import BadHeaderError, send_mail
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse

from gallery.forms import ContactForm
from gallery.models import Album, Image, SimplePage
from gallery.utils import get_prev_next_ids


def home(request):
    """Show about text and array of album thumbnails"""

    try:
        intro = SimplePage.objects.get(slug="intro")
    except SimplePage.DoesNotExist:
        intro = None

    ctx = {"albums": Album.objects.all().order_by("order"), "intro": intro}

    return render(request, "home.html", context=ctx)


def album(request, slug: str):
    """Show about text and array of image thumbnails in this album"""
    album = get_object_or_404(Album, slug=slug)
    images = Image.objects.filter(album=album).order_by("taken")

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
    # flickr = asdict(get_api_image_data(flickr_id))
    img_data = img.get_page_data()
    prev_next_ids = get_prev_next_ids(img)

    ctx = {
        "img": img,
        "img_data": img_data,
        "prev_next_ids": prev_next_ids,
    }

    return render(request, "image.html", context=ctx)


def simple_page(request, page_slug: str):
    """Just render About template"""
    page = get_object_or_404(SimplePage, slug=page_slug)
    return render(request, "about.html", {"page": page})


def contact(request):
    if request.method == "GET":
        form = ContactForm()
    else:
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            your_email = form.cleaned_data["your_email"]
            message = form.cleaned_data["message"]
            try:
                send_mail(subject, message, your_email, settings.MANAGERS, fail_silently=False)
            except BadHeaderError:
                return HttpResponse("Invalid header found.")
            return redirect("contact_success")
    return render(request, "contact.html", {"form": form})


def contact_success(request):
    return render(request, "contact_success.html")


def flush_cache(request, flickr_id: int):
    """Flush the cache for a single image, and redirect to detail view."""

    img = Image.objects.get(flickr_id=flickr_id)
    img.flush_cache()
    return redirect(reverse("image", kwargs={"album_slug": img.album.slug, "flickr_id": flickr_id}))


def refetch(request, flickr_id: int):
    """Re-fetch our db entries for a single image, and redirect to detail view."""

    img = Image.objects.get(flickr_id=flickr_id)
    img.refetch()
    return redirect(reverse("image", kwargs={"album_slug": img.album.slug, "flickr_id": flickr_id}))
