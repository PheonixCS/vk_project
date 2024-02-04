import logging
import uuid
from datetime import timedelta

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from posting.core.horoscopes_images import transfer_horoscope_to_image_object, paste_horoscopes_rates_object
from scraping.models import Horoscope
from tg_core.models.channel import Channel
from tg_core.models.internal_horoscope_source import InternalHoroscopeSource
from tg_core.models.internal_horoscope_source_link import InternalHoroscopeSourceLink
from tg_core.models.tg_attachment import TGAttachment
from tg_core.models.tg_post import TGPost

log = logging.getLogger()


class Command(BaseCommand):
    help = 'Collect tg posts from internal horoscope sources'

    def handle(self, *args, **options):
        print('start collecting')

        for channel in Channel.objects.filter(is_active=True).iterator():
            print(f'work with {channel}')

            internal_horoscope_source = InternalHoroscopeSource.objects.filter(
                channel=channel
            ).first()

            last_day = timezone.now() - timedelta(days=1)

            last_linked = InternalHoroscopeSourceLink.objects.filter(
                link=internal_horoscope_source,
                created_dt__gte=last_day,
            ).values_list('pk', flat=True)

            last_not_linked_horoscopes = Horoscope.objects.filter(
                post_in_group_date__gte=last_day
            ).exclude(
                pk__in=last_linked,
            )

            for horoscope in last_not_linked_horoscopes.iterator():
                log.debug(f'Adding {horoscope}')
                print(f'Adding {horoscope}')

                tg_post = TGPost.objects.create(
                    text=Horoscope.text,
                    channel=channel,
                )

                InternalHoroscopeSourceLink.objects.create(
                    link=internal_horoscope_source,
                    target_post=tg_post,
                    source_post=horoscope
                )

                image_object = transfer_horoscope_to_image_object(horoscope.text)
                image_object = paste_horoscopes_rates_object(image_object)

                TGAttachment.objects.craete(
                    file=File(image_object, uuid.uuid4()),
                    post=tg_post,
                )

                log.debug(f'Done {horoscope}')
                print(f'Done {horoscope}')
