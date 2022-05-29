from django import template
from django.conf import settings
from django.shortcuts import reverse

register = template.Library()


@register.inclusion_tag("thumbnails/album_thumb.html")
def album_thumb(album, *args, **kwargs):
    """Generate data needed for generating an ALBUM thumbnail into
    inclusion template in decorator.
    """
    album_url = reverse("album", kwargs={"slug": album.slug})

    embed_url = (
        album.cat_thumb.get_embed_url(size=settings.FLICKR_THUMBNAIL_SIZE)
        if album.cat_thumb
        else None
    )

    return {"local_url": album_url, "embed_url": embed_url, "title": album.title, "slug": album.slug}
