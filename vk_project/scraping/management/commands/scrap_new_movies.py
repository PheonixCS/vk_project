#  command for manual movie scraping

from scraping.tasks import scrap_new_movies
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        scrap_new_movies.delay()
