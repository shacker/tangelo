import logging

import flickrapi
from django.conf import settings
from django.core.management import call_command

log = logging.getLogger(__name__)


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
