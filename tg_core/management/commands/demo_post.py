import logging

from django.core.management.base import BaseCommand

from posting.core.horoscopes_images import transfer_horoscope_to_image, paste_horoscopes_rates
from scraping.models import Horoscope
from tg_core.tg_logic.bot import send_photo, get_chat_id

log = logging.getLogger()


class Command(BaseCommand):
    help = 'demo'

    def handle(self, *args, **options):
        test_channel = '@netolyrg_test_channel'

        horoscope_record = Horoscope.objects.filter(
            post_in_group_date__isnull=False
        ).first()

        if horoscope_record:
            horoscope_image_name = transfer_horoscope_to_image(horoscope_record.text)
            horoscope_image_name = paste_horoscopes_rates(horoscope_image_name)

            with open(horoscope_image_name, 'rb') as file:
                image = file.read()

            chat_id = get_chat_id(test_channel)
            print(chat_id)

            res = send_photo(
                chat_id=chat_id.id,
                photo=image,
                caption='test',
            )
            print(res)
