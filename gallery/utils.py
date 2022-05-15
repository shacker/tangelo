from django.conf import settings
import flickrapi
from dataclasses import dataclass
from django.conf import settings


@dataclass
class ImageData:
    """Class for storing usable datapoints needed for displaying a Flickr image.
    Cast back to a dict before sending to template. """

    title: str
    description: str
    embed_url: str
    page_url: str


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
    server = photo["server"]
    secret = photo["secret"]
    embed_url = f"https://live.staticflickr.com/{server}/{flickr_id}_{secret}_{size}.jpg"

    image_data = ImageData(
        title=photo["title"]["_content"],
        description=photo["description"]["_content"],
        page_url=photo["urls"]["url"][0]["_content"],
        embed_url=embed_url,
    )

    return image_data
