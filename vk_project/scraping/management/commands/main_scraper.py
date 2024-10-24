#  command for manual main scraping

from scraping.tasks import run_scraper
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run main scrapper asynchronously'

    def handle(self, *args, **options):
        run_scraper.delay()
