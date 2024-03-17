import logging

from django.core.management.base import BaseCommand

from tg_core.models.tg_post import TGPost
from tg_core.post_logic.poster import Poster
from tg_core.tg_logic.adapter import TGUniversalPost

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'demo'

    def handle(self, *args, **options):
        tg_posts = TGPost.objects.filter(status=TGPost.DRAFT)

        for tg_post in tg_posts:
            post = TGUniversalPost(tg_post)
            result = Poster.post(post)
            print(result)
