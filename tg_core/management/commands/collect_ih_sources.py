import logging
import uuid
from datetime import timedelta
from io import BytesIO
from typing import Collection

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
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
        log.info('start collecting')

        for channel in Channel.objects.filter(is_active=True).iterator():
            print(f'work with {channel}')

            internal_horoscope_sources: Collection[InternalHoroscopeSource] = InternalHoroscopeSource.objects.filter(
                channel=channel
            )

            last_day = timezone.now() - timedelta(days=7)
            print(last_day)

            for internal_horoscope_source in internal_horoscope_sources:
                print(f'work with {internal_horoscope_source}')

                link_objects = InternalHoroscopeSourceLink.objects.filter(
                    link=internal_horoscope_source,
                    created_dt__gte=last_day,
                    source_post__isnull=False
                )

                if link_objects.exists() and link_objects.count() >= 1:
                    last_linked = link_objects.values_list('source_post', flat=True)

                    print(last_linked)

                    last_not_linked_horoscopes = Horoscope.objects.filter(
                        add_to_db_date__gte=last_day,
                        group=internal_horoscope_source.group
                    ).exclude(
                        pk__in=last_linked,
                    )
                else:
                    last_not_linked_horoscopes = Horoscope.objects.filter(
                        add_to_db_date__gte=last_day,
                        group=internal_horoscope_source.group
                    )

                print(last_not_linked_horoscopes)

                for horoscope in last_not_linked_horoscopes.iterator():
                    log.debug(f'Adding {horoscope}')
                    print(f'Adding {horoscope}')

                    tg_post = TGPost.objects.create_from_source(
                        horoscope, channel, internal_horoscope_source
                    )

                    image_object = transfer_horoscope_to_image_object(horoscope.text)
                    image_object = paste_horoscopes_rates_object(image_object, original_rates=horoscope.rates)

                    buffer = BytesIO()
                    image_object.save(buffer, format='JPEG')
                    image_object = ContentFile(buffer.getvalue())

                    print('ready to paste django file')

                    django_file = InMemoryUploadedFile(
                        image_object,
                        None,
                        f'{str(uuid.uuid4())}.jpg',
                        'image/jpeg',
                        image_object.tell,
                        None
                    )

                    TGAttachment.objects.create(
                        file=django_file,
                        post=tg_post,
                    )

                    log.debug(f'Done {horoscope}')
                    print(f'Done {horoscope}')
