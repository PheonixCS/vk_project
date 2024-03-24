import re

from posting.models import Group
import logging
from scraping.models import Horoscope, Attachment
from django.utils import timezone
from datetime import timedelta

log = logging.getLogger('scraping.core.horoscopes')


def fetch_zodiac_sign(text):
    zodiac_signs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева',
                    'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
    for zodiac_sign in zodiac_signs:
        if zodiac_sign.lower() in text.lower():
            return zodiac_sign.lower()
    return None


def find_horoscopes(records):
    horoscopes_records = []
    for record in records:
        text = record.get('text')
        if text:
            first_line = text.splitlines()[0]
        else:
            continue

        if fetch_zodiac_sign(first_line) and bool(re.search(r'\d', first_line)):
            horoscopes_records.append(record)

    return horoscopes_records


def horoscopes_translate(name, to_lang='ru'):
    signs_map = {
        'arises': 'овен',
        'taurus': 'телец',
        'gemini': 'близнецы',
        'cancer': 'рак',
        'leo': 'лев',
        'virgo': 'дева',
        'libra': 'весы',
        'scorpio': 'скорпион',
        'sagittarius': 'стрелец',
        'capricorn': 'козерог',
        'aquarius': 'водолей',
        'pisces': 'рыбы'
    }

    if to_lang == 'en':
        signs_map = dict((v, k) for k, v in signs_map.items())

    return signs_map.get(name)


def save_horoscope_record_to_db(group, text, zodiac_sign):
    log.info('save_horoscope_record_to_db called')
    obj, created = Horoscope.objects.get_or_create(
        group=group,
        zodiac_sign=zodiac_sign,
        defaults={
            'text': text,
        }
    )
    if created:
        log.info(f'horoscope created for group {group.group_id}')

    return created


def save_horoscope_for_main_groups(horoscope: Horoscope, image_vk_url: str, group_id: int, record_id: int) -> None:
    log.info('save_horoscope_for_main_groups called')
    main_horoscopes = Group.objects.filter(group_type=Group.HOROSCOPES_MAIN)
    log.debug(f'Main horoscopes: {main_horoscopes}')

    # https://trello.com/c/uB0RQBvE/244
    copyright_text = f'https://vk.com/club{group_id}?w=wall-{group_id}_{record_id}'

    for group in main_horoscopes:
        horoscope_obj, created = Horoscope.objects.get_or_create(
            group=group,
            zodiac_sign=horoscope.zodiac_sign,
            defaults={
                'text': horoscope.text,
                'copyright_text': copyright_text
            }
        )
        if created:
            log.info('horoscope created')

            Attachment.objects.create(
                data_type=Attachment.PICTURE,
                h_record=horoscope_obj,
                vk_attachment_id=image_vk_url
            )
    log.info('save_horoscope_for_main_groups finished')


def are_horoscopes_for_main_groups_ready(group=None):
    if not group:
        main_horoscopes = Group.objects.filter(group_type=Group.HOROSCOPES_MAIN)
    else:
        main_horoscopes = [group, ]
    start_of_a_day = timezone.now().replace(hour=0, minute=0, second=0)

    result = []

    for group in main_horoscopes:
        horoscopes = Horoscope.objects.filter(group=group, add_to_db_date__gte=start_of_a_day)

        result.append(len(horoscopes) == 12)

    are_ready = all(result) if result else False
    log.info(f'are_horoscopes_for_main_groups_ready result is {are_ready}')
    return are_ready
