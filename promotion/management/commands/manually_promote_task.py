from django.core.management.base import BaseCommand
from promotion.tasks.promotion_task import add_promotion_task


class Command(BaseCommand):
    help = 'Manually send post to promotion'

    def add_arguments(self, parser):
        parser.add_argument('post_url', type=str)

    def handle(self, *args, **options):
        url = options['post_url']
        add_promotion_task.delay(url)

