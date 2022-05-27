from dataclasses import dataclass
from datetime import datetime

import flickrapi
from dateutil import parser
from django.conf import settings


@dataclass
class ImageData:
    """Class for storing usable datapoints needed for displaying a Flickr image.
    Cast back to a dict before sending to template."""

    title: str
    description: str
    embed_url: str
    page_url: str
    taken: datetime
    raw_data: dict


def get_api_image_data(flickr_id: int, size: str = settings.FLICKR_IMAGE_SIZE):
    """
    Use Flickr's getInfo() API to get metadata about an image by ID.
    https://www.flickr.com/services/api/flickr.photos.getInfo.html

    See also: Flickr URL guidelines:
    https://www.flickr.com/services/api/misc.urls.html

    Image size defaults to "b" i.e. 1024 on the long side.

    Args:
        flickr_id: int
        size: Optional suffix mapping, per URL docs - defaults to 1024 on the long side

    Returns
        ImageData dataclass instance as above
    """

    flickr = flickrapi.FlickrAPI(
        settings.FLICKR_API_KEY, settings.FLICKR_API_SECRET, format="parsed-json"
    )
    response = flickr.photos.getInfo(photo_id=flickr_id)
    photo = response["photo"]
    try:
        taken = parser.parse(response["photo"]["dates"]["taken"])
    except:
        taken = None

    # Here store full response, parse out date

    server = photo["server"]
    secret = photo["secret"]
    embed_url = f"https://live.staticflickr.com/{server}/{flickr_id}_{secret}_{size}.jpg"

    # TODO Ditch the dataclass, just return the raw response for storage, get the rest of fields from our own db
    image_data = ImageData(
        title=photo["title"]["_content"],
        description=photo["description"]["_content"],
        page_url=photo["urls"]["url"][0]["_content"],
        embed_url=embed_url,
        taken=taken,
        raw_data=response
    )

    return image_data


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
