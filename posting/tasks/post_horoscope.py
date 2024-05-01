import logging

import vk_api
from celery import shared_task
from constance import config
from django.utils import timezone

from posting.core.files import download_file, delete_files
from posting.core.horoscopes_images import transfer_horoscope_to_image, paste_horoscopes_rates
from posting.core.vk_helper import create_ad_record
from posting.models import Group
from promotion.tasks.promotion_task import add_promotion_task
from scraping.core.horoscopes import save_horoscope_for_main_groups
from scraping.models import Horoscope
from services.text_utilities import replace_russian_with_english_letters, delete_hashtags_from_text
from services.vk.auth_with_access_token import create_vk_session_with_access_token
from services.vk.files import upload_photos
from services.vk.vars import ADVERTISEMENT_ERROR_CODE

log = logging.getLogger('posting.scheduled')
telegram = logging.getLogger('telegram')


@shared_task
def post_horoscope(group_id: int, horoscope_record_id: int):
    log.debug('start posting horoscopes in {} group'.format(group_id))
    group = Group.objects.get(group_id=group_id)

    session = create_vk_session_with_access_token(group.user)
    if not session:
        log.error('session not created in group {}'.format(group_id))
        return

    api = session.get_api()
    if not api:
        log.error('no api was created in group {}'.format(group_id))
        return

    horoscope_record: Horoscope = group.horoscopes.get(pk=horoscope_record_id)
    log.debug('{} horoscope record to post in {}'.format(horoscope_record.id, group.domain_or_id))

    try:
        attachments = []

        record_text = horoscope_record.text

        if config.HOROSCOPES_TO_IMAGE_ENABLED:
            horoscope_image_name = transfer_horoscope_to_image(record_text)
            horoscope_image_name = paste_horoscopes_rates(horoscope_image_name, original_rates=horoscope_record.rates)
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

        # https://trello.com/c/uB0RQBvE/24
        if group.group_type == Group.HOROSCOPES_MAIN:
            record_text = ''

        if config.SHOW_AUTHOR:
            from_group = 0
            signed = 1
        else:
            from_group = 1
            signed = 0

        # posting part
        attachments_string = ','.join(attachments)
        data_to_post = {
            'owner_id': '-{}'.format(group_id),
            'from_group': from_group,
            'signed': signed,
            'message': record_text,
            'attachments': attachments_string
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
                    post_id=record_id)
            except vk_api.VkApiError:
                log.warning(f'Failed to pin horoscope', exc_info=True)
            else:
                log.debug(f'Pin horoscope result {pin_response}')

                # if config.BLOCKS_ACTIVE:
                #     posting_block = group.blocks.filter(reason=Block.POSTING, is_active=True).first()
                #     posting_block.deactivate()

            # Promotion https://trello.com/c/pLZ9LAlF/275
            record_url = f'{group.url}?w=wall-{group_id}_{record_id}'
            add_promotion_task.delay(record_url)

    except vk_api.ApiError as error_msg:
        log.error('group {} got api error: {}'.format(group_id, error_msg))

        if error_msg.code == ADVERTISEMENT_ERROR_CODE:
            create_ad_record(-1, group, timezone.now())

        return
    except:
        log.error('caught unexpected exception in group {}'.format(group_id), exc_info=True)
        telegram.critical('Неожиданная ошибка при постинге гороскопов')
        return

    horoscope_record.post_in_group_date = timezone.now()
    horoscope_record.save()

    if group.group_type == Group.HOROSCOPES_COMMON:
        save_horoscope_for_main_groups(horoscope_record, attachments_string, int(group_id), int(record_id))

    log.debug('post horoscopes in group {} finished'.format(group_id))
