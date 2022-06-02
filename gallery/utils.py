import logging

import flickrapi
from django.conf import settings
from django.core.management import call_command

log = logging.getLogger(__name__)


def get_api_image_data(flickr_id: int):
    """
    Use Flickr's getInfo() API to get metadata about an image by ID.
    https://www.flickr.com/services/api/flickr.photos.getInfo.html

    Args:
        flickr_id: int

    Returns
        Raw API response data
    """

    flickr = flickrapi.FlickrAPI(
        settings.FLICKR_API_KEY, settings.FLICKR_API_SECRET, format="parsed-json"
    )
    response = flickr.photos.getInfo(photo_id=flickr_id)
    return response


def get_prev_next_ids(img):
    """Given an Image instance, finds the previous and next
        Image IDs in an album, based on `taken` (date taken).
        n.b. Originally written to order by manual `album_order`
        but decided I preferred simple auto date ordering to keep things fresh.

    Returns:
        {"prev": prev_id, "next": next_id}
        Either of these can be None if there is no previous or next.
    """

    from gallery.models import Image

    next_id = None
    prev_id = None

    # Start with a queryset of all images in this image's album, except self
    qs = Image.objects.filter(album=img.album).exclude(flickr_id=img.flickr_id)

    next_id_qs = qs.filter(taken__lt=img.taken).order_by("-taken")
    if next_id_qs.exists():
        next_id = next_id_qs.first().flickr_id

    prev_id_qs = qs.filter(taken__gt=img.taken).order_by("taken")
    if prev_id_qs.exists():
        prev_id = prev_id_qs.first().flickr_id

    return {"prev": prev_id, "next": next_id}


def nuclear(clear: bool = True, refetch: bool = False):
    """Depending on args:
    Clears all caches (default True)
    Refetch all API data from Flickr (default False)
    """
    log.info("Flusing all caches")
    call_command("clear_cache")
    log.info("Done clearing cache.")

    if refetch:
        """Rarely needed -"""
        from gallery.models import Image

        for image in Image.objects.all():
            log.info(f"Re-fetching API data for image {image.flickr_id}")
            image.refetch()
            image.save()

        log.info("Done re-fetching")
