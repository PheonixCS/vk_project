import logging
from random import shuffle

import vk_api
from celery import shared_task
from constance import config
from django.utils import timezone

from posting.core.images import sort_images_for_movies, is_all_images_not_horizontal, merge_six_images_into_one, \
    is_text_on_image
from posting.core.poster import prepare_audio_attachments, prepare_image_for_posting, \
    find_next_element_by_last_used_id
from posting.core.files import download_file, delete_files
from services.text_utilities import delete_hashtags_from_text, delete_emoji_from_text, \
    replace_russian_with_english_letters
from posting.models import Group, Block
from scraping.models import Record
from services.vk.core import create_vk_session_using_login_password
from services.vk.files import upload_photos, check_docs_availability, check_video_availability
from services.vk.vars import ADVERTISEMENT_ERROR_CODE
from posting.core.vk_helper import create_ad_record

log = logging.getLogger('posting.scheduled')
telegram = logging.getLogger('telegram')


@shared_task(time_limit=60)
def post_record(group_id, record_id):
    log.debug('start posting in {} group'.format(group_id))

    group = Group.objects.get(group_id=group_id)
    record = Record.objects.get(pk=record_id)

    try:
        session = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id)
        api = session.get_api()
    except:
        log.error('got unexpected exception in post_record for group {}'.format(group_id), exc_info=True)
        record.set_failed()
        return

    if not session:
        log.error('session not created in group {}'.format(group_id))
        record.set_failed()
        return

    if not api:
        log.error('no api was created in group {}'.format(group_id))
        record.set_failed()
        return

    try:
        attachments = []
        actions_to_unique_image = {}

        images = sorted(list(record.images.all()), key=lambda x: x.index_number)
        gifs = record.gifs.all()
        videos = record.videos.all()
        record_text = record.text
        copyright_text = ''

        if group.is_copyright_needed or record.donor.is_copyright_needed:
            copyright_text = f'https://vk.com/club{record.donor.id}?w=wall-{record.donor.id}_{record.record_id}'

        record_text = delete_hashtags_from_text(record_text)

        text_to_image_condition = (len(images) == 1
                                   and group.is_text_filling_enabled
                                   and len(record_text) <= config.MAX_TEXT_TO_FILL_LENGTH)

        if group.is_text_delete_enabled:
            record_text = ''

        if text_to_image_condition:
            actions_to_unique_image['text_to_fill'] = delete_emoji_from_text(record_text)
            record_text = ''

        # audios part
        audios = list(record.audios.all())
        log.debug('got {} audios for group {}'.format(len(audios), group_id))
        # cut audio list to prevent overflow
        if len(audios) == 9:
            audios = audios[:-1]
        log.debug('got {} audios for group {} after cutting'.format(len(audios), group_id))

        prepared_audios = prepare_audio_attachments(audios,
                                                    is_shuffle=group.is_audios_shuffle_enabled,
                                                    is_cut=config.CUT_ONE_AUDIO_ATTACHMENT
                                                    )
        attachments.extend(prepared_audios)

        # images part
        if group.is_replace_russian_with_english and not text_to_image_condition:
            record_text = replace_russian_with_english_letters(record_text)

        if group.is_merge_images_enabled:
            images = images[:6]

        log.debug('got {} images for group {}'.format(len(images), group_id))

        if group.is_photos_shuffle_enabled and len(images) > 1:
            shuffle(images)
            log.debug('group {} {} images shuffled'.format(group_id, len(images)))

        image_files = [download_file(image.url) for image in images]

        if group.group_type == group.MOVIE_COMMON:
            image_files = sort_images_for_movies(image_files)

        merge_six_images_condition = (
                group.is_merge_images_enabled
                and len(images) == 6
                and is_all_images_not_horizontal(image_files)
        )
        if merge_six_images_condition:
            old_image_files = image_files
            image_files = [merge_six_images_into_one(image_files)]
            delete_files(old_image_files)

        check_text = len(image_files) < 4

        for image_local_filename in image_files:
            image_has_text = check_text and not is_text_on_image(image_local_filename)

            if group.is_image_mirror_enabled and not image_has_text:
                actions_to_unique_image['mirror'] = True

            if group.RGB_image_tone:
                actions_to_unique_image['rgb_tone'] = group.RGB_image_tone

            crop_image_condition = (
                    not group.is_merge_images_enabled
                    and group.is_changing_image_to_square_enabled
                    and not image_has_text
            )
            if crop_image_condition:
                percentage_to_crop_from_edges = config.PERCENTAGE_TO_CROP_FROM_EDGES
                actions_to_unique_image['crop_to_square'] = percentage_to_crop_from_edges

            prepare_image_for_posting(image_local_filename, **actions_to_unique_image)

        if image_files:
            attachments.extend(upload_photos(session, image_files, group_id))
            delete_files(image_files)

        # gif part
        log.debug('got {} gifs for group {}'.format(len(gifs), group_id))
        if gifs and check_docs_availability(api, ['{}_{}'.format(gif.owner_id, gif.gif_id) for gif in gifs]):
            for gif in gifs:
                attachments.append('doc{}_{}'.format(gif.owner_id, gif.gif_id))
        elif gifs:
            log.warning('Failed to post because of gif unavailability')
            record.set_failed()
            return

        # video part
        log.debug('got {} videos in attachments for group {}'.format(videos, group_id))
        for video in videos:
            if check_video_availability(api, video.owner_id, video.video_id):
                attachments.append('video{}_{}'.format(video.owner_id, video.video_id))
            else:
                log.warning('Failed to post because of video unavailability')
                record.set_failed()
                return

        # additional texts
        additional_texts = group.additional_texts.all().order_by('id')
        if group.is_additional_text_enabled and additional_texts:
            additional_text = find_next_element_by_last_used_id(group.additional_texts.all().order_by('id'),
                                                                group.last_used_additional_text_id)
            log.debug(f'Found additional texts for group {group.domain_or_id}. '
                      f'Last used text id: {group.last_used_additional_text_id}, '
                      f'new text id: {additional_text.id}, new text: {additional_text.text},'
                      f'new text plural: {additional_text.text_plural}')

            group.last_used_additional_text_id = additional_text.id
            group.save(update_fields=['last_used_additional_text_id'])

            text_to_add = additional_text.text if len(images) <= 1 else additional_text.text_plural

            record_text = '\n'.join([record_text, text_to_add]) if record_text else text_to_add

        # to fight double images
        attachments.reverse()
        log.debug(f'{group_id} attachments: {attachments}')
        # posting part
        data_to_post = {
            'owner_id': f'-{group_id}',
            'from_group': 1,
            'message': record_text,
            'attachments': ','.join(attachments)
        }

        if copyright_text:
            data_to_post['copyright'] = copyright_text

        post_response = api.wall.post(**data_to_post)

        if config.BLOCKS_ACTIVE:
            posting_block = group.blocks.filter(reason=Block.POSTING, is_active=True).first()
            posting_block.deactivate()

        log.debug('{} in group {}'.format(post_response, group_id))
    except vk_api.ApiError as error_msg:
        log.error('group {} got api error: {}'.format(group_id, error_msg))

        if error_msg.code == ADVERTISEMENT_ERROR_CODE:
            record.set_ready()
            now = timezone.now()
            _result = create_ad_record(-1, group, now)
            log.debug(f'create_ad_record result = {_result}')
        else:
            record.set_failed()

        return
    except:
        log.error('caught unexpected exception in group {}'.format(group_id), exc_info=True)
        telegram.critical('Неожиданная ошибка при обычном постинге')
        record.set_failed()
        return

    record.post_in_group_id = post_response.get('post_id', 0)
    record.post_in_group_date = timezone.now()
    record.group = group
    record.status = Record.POSTED
    record.change_status_time = timezone.now()

    fields = ['post_in_group_id', 'post_in_group_date', 'group', 'status', 'change_status_time']
    record.save(update_fields=fields)

    log.debug(f'Post in group {group_id} <{group.name}> finished')
