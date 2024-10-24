# manually download youtube trailers

from django.core.management.base import BaseCommand

from scraping.tasks import download_youtube_trailers


class Command(BaseCommand):
    def handle(self, *args, **options):
        download_youtube_trailers.delay()
