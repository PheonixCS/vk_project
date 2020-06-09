#
import re
import ast

from scraping.core.scraper import log
from scraping.models import Horoscope, Attachment
from posting.models import Group

from constance import config


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
        log.info('horoscope created')

    return created


# FIXME need tests
def save_horoscope_for_main_groups(horoscope: Horoscope, image_vk_url: str, group_id: int, record_id: int) -> None:
    log.info('save_horoscope_record_to_db called')
    main_horoscope_ids = ast.literal_eval(config.MAIN_HOROSCOPES_IDS)

    # https://trello.com/c/uB0RQBvE/244
    copyright_text = f'https://vk.com/club{group_id}?w=wall-{group_id}_{record_id}'

    for group_id in main_horoscope_ids:

        group = Group.objects.get(group_id=group_id)

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
