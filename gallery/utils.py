import flickrapi
from django.conf import settings


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
        Image IDs in an album, based on `album_order`.

    Returns:
        {"prev": prev_id, "next": next_id}
        Either of these can be None if there is no previous or next.
    """

    from gallery.models import Image

    next_id = None
    prev_id = None

    # Start with a queryset of all images in this image's album, except self
    qs = Image.objects.filter(album=img.album).exclude(flickr_id=img.flickr_id)

    next_id_qs = qs.filter(album_order__gt=img.album_order).order_by("album_order")
    if next_id_qs.exists():
        next_id = next_id_qs.first().flickr_id

    prev_id_qs = qs.filter(album_order__lt=img.album_order).order_by("-album_order")
    if prev_id_qs.exists():
        prev_id = prev_id_qs.first().flickr_id

    return {"prev": prev_id, "next": next_id}
