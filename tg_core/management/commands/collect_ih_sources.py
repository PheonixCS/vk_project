import logging

from django.core.management.base import BaseCommand

log = logging.getLogger()


class Command(BaseCommand):
    help = 'demo'

    def handle(self, *args, **options):
        pass
