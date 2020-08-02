import ast
import logging

import vk_api
from celery import shared_task
from constance import config
from django.utils import timezone

from posting.core.horoscopes import generate_special_group_reference
from posting.core.horoscopes_images import transfer_horoscope_to_image
from posting.core.files import download_file, delete_files
from services.text_utilities import replace_russian_with_english_letters, delete_hashtags_from_text
from posting.models import Group
from scraping.core.horoscopes import fetch_zodiac_sign, save_horoscope_for_main_groups
from services.vk.core import create_vk_session_using_login_password
from services.vk.files import upload_photos

log = logging.getLogger('posting.scheduled')
telegram = logging.getLogger('telegram')


@shared_task
def post_horoscope(group_id: int, horoscope_record_id: int):
    log.debug('start posting horoscopes in {} group'.format(group_id))
    group = Group.objects.get(group_id=group_id)
    session = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id)
    if not session:
        log.error('session not created in group {}'.format(group_id))
        return

    api = session.get_api()
    if not api:
        log.error('no api was created in group {}'.format(group_id))
        return

    main_horoscope_ids = ast.literal_eval(config.MAIN_HOROSCOPES_IDS)

    horoscope_record = group.horoscopes.get(pk=horoscope_record_id)
    log.debug('{} horoscope record to post in {}'.format(horoscope_record.id, group.domain_or_id))

    try:
        attachments = []

        record_text = horoscope_record.text

        if config.HOROSCOPES_TO_IMAGE_ENABLED:
            horoscope_image_name = transfer_horoscope_to_image(record_text)
            attachments.extend(upload_photos(session, horoscope_image_name, str(group_id)))
            delete_files(horoscope_image_name)
            record_text = ''
        else:
            if group.is_replace_russian_with_english:
                record_text = replace_russian_with_english_letters(record_text)

            record_text = delete_hashtags_from_text(record_text)

            if horoscope_record.image_url and not config.HOROSCOPES_TO_IMAGE_ENABLED:
                image_local_filename = download_file(horoscope_record.image_url)
                attachments.extend(upload_photos(session, image_local_filename, str(group_id)))
                delete_files(image_local_filename)

        group_zodiac_sign = fetch_zodiac_sign(group.name)
        if not group_zodiac_sign:
            text_to_add = generate_special_group_reference(horoscope_record.text)
            record_text = '\n'.join([text_to_add, record_text]) if record_text else text_to_add

        # https://trello.com/c/uB0RQBvE/24
        if group.group_type == Group.HOROSCOPES_MAIN:
            record_text = ''

        # posting part
        data_to_post = {
            'owner_id': '-{}'.format(group_id),
            'from_group': 1,
            'message': record_text,
            'attachments': ','.join(attachments)
        }

        # https://trello.com/c/uB0RQBvE/24
        if group.group_type == Group.HOROSCOPES_MAIN:
            data_to_post['copyright'] = horoscope_record.copyright_text

        post_response = api.wall.post(**data_to_post)
        log.debug('{} in group {}'.format(post_response, group_id))

        record_id = post_response.get('post_id')

        if group.group_type == Group.HOROSCOPES_COMMON:
            try:
                pin_response = api.wall.pin(
                    owner_id='-{}'.format(group.group_id),
                    post_id=post_response.get('post_id'))
            except vk_api.VkApiError:
                log.warning(f'Failed to pin horoscope', exc_info=True)
            else:
                log.debug(f'Pin horoscope result {pin_response}')

    except vk_api.VkApiError as error_msg:
        log.info('group {} got api error: {}'.format(group_id, error_msg))
        return
    except:
        log.error('caught unexpected exception in group {}'.format(group_id), exc_info=True)
        telegram.critical('Неожиданная ошибка при постинге гороскопов')
        return

    horoscope_record.post_in_group_date = timezone.now()
    horoscope_record.save()

    if group_id not in main_horoscope_ids:
        save_horoscope_for_main_groups(horoscope_record, attachments, int(group_id), int(record_id))

    log.debug('post horoscopes in group {} finished'.format(group_id))
