from typing import Tuple, Optional

import vk_api
from constance import config

from posting.core.files import delete_files, download_file
from posting.core.horoscopes_images import transfer_horoscope_to_image, paste_horoscopes_rates
from posting.models import Group
from scraping.core.horoscopes import fetch_zodiac_sign
from scraping.models import Horoscope
from services.text_utilities import replace_russian_with_english_letters, delete_hashtags_from_text
from services.vk.files import upload_photos


def fetch_date_from_horoscope_text(raw_text):
    return raw_text.split('\n')[0].split(', ')[0]


def generate_special_group_reference(horoscope_text):
    replace_map = {
        'Овен': 'Овна',
        'Телец': 'Тельца',
        'Близнецы': 'Близнеца',
        'Рак': 'Рака',
        'Лев': 'Льва',
        'Дева': 'Девы',
        'Весы': 'Весов',
        'Скорпион': 'Скорпиона',
        'Стрелец': 'Стрельца',
        'Козерог': 'Козерога',
        'Водолей': 'Водолея',
        'Рыбы': 'Рыбы',
    }

    special_group_zodiac_zign = fetch_zodiac_sign(horoscope_text.splitlines()[0]).capitalize()
    # special_group_id = Group.objects.filter(name=special_group_zodiac_zign).first().domain_or_id
    horoscope_date = fetch_date_from_horoscope_text(horoscope_text)

    # return f'[club{special_group_id}|' \
    #        f'Гороскоп для {replace_map[special_group_zodiac_zign]}] ' \
    #        f'на {horoscope_date}'

    return f'Гороскоп для {replace_map[special_group_zodiac_zign]} ' \
           f'на {horoscope_date}.'


def prepare_record_content(session: vk_api.VkApi, group: Group, horoscope_record: Horoscope) -> Tuple[str, list]:
    if config.HOROSCOPES_TO_IMAGE_ENABLED:
        final_record_text, filename_to_upload = prepare_horoscope_with_image(horoscope_record)
    elif config.HOROSCOPES_CUT_ENABLED:
        final_record_text, filename_to_upload = prepare_horoscope_cut(group, horoscope_record)
    else:
        final_record_text, filename_to_upload = prepare_common(group, horoscope_record)

    # old rule, source unknown
    if group.group_type == Group.HOROSCOPES_MAIN:
        final_record_text = ''

    attachments = []
    if filename_to_upload:
        attachments = upload_photos(session, filename_to_upload, str(group.group_id))
        delete_files(filename_to_upload)

    return final_record_text, attachments


# TODO add tests
def prepare_common(group: Group, horoscope_record: Horoscope) -> Tuple[str, Optional[str]]:
    # original text is fine
    final_record_text = horoscope_record.text

    if group.is_replace_russian_with_english:
        final_record_text = replace_russian_with_english_letters(final_record_text)

    final_record_text = delete_hashtags_from_text(final_record_text)

    # prepare attachment
    if horoscope_record.image_url and not config.HOROSCOPES_TO_IMAGE_ENABLED:  # idk what is "image_url" originally
        filename_to_upload = download_file(horoscope_record.image_url)
    else:
        filename_to_upload = None

    return final_record_text, filename_to_upload


# TODO add tests
def prepare_horoscope_with_image(horoscope_record: Horoscope) -> Tuple[str, str]:
    # not text with custom horoscope
    final_record_text = ''

    # prepare attachment
    horoscope_image_name = transfer_horoscope_to_image(horoscope_record.text)
    filename_to_upload = paste_horoscopes_rates(horoscope_image_name, original_rates=horoscope_record.rates)

    return final_record_text, filename_to_upload


def prepare_horoscope_cut(group: Group, horoscope_record: Horoscope) -> Tuple[str, Optional[str]]:
    # cut 50% and add link text
    original = horoscope_record.text
    words = original.split(' ')
    cut = ' '.join(words[:len(words)//2])
    final_record_text = f'{cut}... {group.horoscope_postfix}'

    # attachments
    filename_to_upload = None
    return final_record_text, filename_to_upload
