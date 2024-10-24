import logging

from django.core.management.base import BaseCommand

from tg_core.models.tg_post import TGPost
from tg_core.post_logic.poster import Poster
from tg_core.tg_logic.adapter import TGUniversalPost

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'post scheduled posts'

    def handle(self, *args, **options):
        tg_posts = TGPost.scheduled_now.all()

        if tg_posts.count() > 0:
            for tg_post in tg_posts:
                log.info(f'got scheduled {tg_post}')
                post = TGUniversalPost(tg_post)
                result = Poster.post(post)
                log.info(result)
        else:
            log.info('no scheduled posts right now')
