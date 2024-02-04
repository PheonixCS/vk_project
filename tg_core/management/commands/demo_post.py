import logging

from django.core.management.base import BaseCommand

from posting.core.horoscopes_images import transfer_horoscope_to_image, paste_horoscopes_rates
from scraping.models import Horoscope
from tg_core.models.channel import Channel
from tg_core.models.tg_post import TGPost
from tg_core.post_logic.poster import Poster
from tg_core.tg_logic.adapter import TGUniversalPost
from tg_core.tg_logic.bot import send_photo, get_chat_id

log = logging.getLogger()


class Command(BaseCommand):
    help = 'demo'

    def handle(self, *args, **options):
        tg_post: TGPost = TGPost.objects.filter(status=TGPost.DRAFT)

        if tg_post:
            post = TGUniversalPost(tg_post)
            result = Poster.post(post)
            print(result)
