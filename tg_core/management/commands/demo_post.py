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
        test_channel = '@netolyrg_test_channel'

        horoscope_record: Horoscope = Horoscope.objects.filter(
            post_in_group_date__isnull=False
        ).first()

        if horoscope_record:
            horoscope_image_name = transfer_horoscope_to_image(horoscope_record.text)
            horoscope_image_name = paste_horoscopes_rates(horoscope_image_name)

            chat_id = get_chat_id(test_channel)
            print(chat_id)

            channel, _ = Channel.objects.update_or_create(
                tg_id=chat_id.id,
                defaults=dict(
                    name=test_channel,
                ),
            )

            tg_object = TGPost.objects.create(
                text=horoscope_record.zodiac_sign,
                channel=channel,
            )

            post = TGUniversalPost(tg_object)

            with open(horoscope_image_name, 'rb') as file:
                image = file.read()
                post.attachments.append(image)

            result = Poster(channel.tg_id).post(post)
            print(result)
