from django import template
from django.conf import settings
from django.shortcuts import reverse

register = template.Library()


@register.inclusion_tag("_thumbnail.html")
def render_thumbnail(img, *args, **kwargs):
    """Generate data needed for generating a thumbnail and render it into
    inclusion template  `_thumbnail.html`
    """
    local_url = reverse("image", kwargs={"album_slug": img.album.slug, "flickr_id": img.flickr_id})
    embed_url = img.get_embed_url(size=settings.FLICKR_THUMBNAIL_SIZE)

    return {
        "local_url": local_url,
        "embed_url": embed_url,
        "title": img.title
    }
