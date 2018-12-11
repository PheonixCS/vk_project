# This command solve 152 task problem: parse

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'fix trailers that was uploaded in vk but got no vk_url'

    def add_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--group_id',
            default='27045802',
            help='id of the group'
        )

    def handle(self, *args, **options):
        pass
