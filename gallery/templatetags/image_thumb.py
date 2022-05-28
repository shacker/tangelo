from threading import local
from django import template
from django.conf import settings
from django.shortcuts import reverse

register = template.Library()

from icecream import ic

@register.inclusion_tag("thumbnails/image_thumb.html")
def image_thumb(img, *args, **kwargs):
    """Generate data needed for generating an IMAGE thumbnail into
    inclusion template in decorator.
    """
    local_url = reverse("image", kwargs={"album_slug": img.album.slug, "flickr_id": img.flickr_id})
    embed_url = img.get_embed_url(size=settings.FLICKR_THUMBNAIL_SIZE)
    return {
        "local_url": local_url,
        "embed_url": embed_url,
        "title": img.title
    }
