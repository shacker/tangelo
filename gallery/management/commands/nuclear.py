import logging

from django.core.management.base import BaseCommand, CommandParser
from gallery.utils import nuclear

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """Nuclear option - wipes all caches by default. With `refetch=True`,
    also rewrites Flickr API data on each Image model."""

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "-r",
            "--refetch",
            dest="refetch_images",
            default=False,
            help="If True, refetches image data",
        )

    def handle(self, *args, **options) -> None:
        """Do it!"""
        if options.get("refetch_images"):
            nuclear(refetch=True)
        else:
            # Default behavior is to clear cache without refetching
            nuclear()
