from gallery.models import Album


def nav_albums_list(request):
    """Make the set of active Albums available on all pages
    for use in the navigation dropdown.
    """
    albums = Album.objects.all().order_by("title")
    return {"global_albums": albums}
