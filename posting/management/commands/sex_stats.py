#  command for manual main scraping

from posting.tasks.sex_statistics_weekly import sex_statistics_weekly
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'gather sex stats'

    def handle(self, *args, **options):
        sex_statistics_weekly()
