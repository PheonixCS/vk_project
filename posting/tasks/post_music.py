import logging
import os

from celery import shared_task
from constance import config
from django.conf import settings
from django.utils import timezone

from posting.core.images import paste_abstraction_on_template, paste_text_on_music_image
from posting.core.poster import prepare_audio_attachments, get_music_compilation_artist, get_music_compilation_genre, \
    find_next_element_by_last_used_id
from posting.core.files import download_file, delete_files
from services.text_utilities import delete_emoji_from_text
from posting.models import Group, BackgroundAbstraction
from scraping.models import Record
from services.vk.core import create_vk_session_using_login_password
from services.vk.files import upload_photos

log = logging.getLogger('posting.scheduled')
telegram = logging.getLogger('telegram')


@shared_task(time_limit=60)
def post_music(group_id, record_id):
    log.debug(f'start posting music in group {group_id}')

    group = Group.objects.get(group_id=group_id)
    record = Record.objects.get(pk=record_id)

    try:
        session = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id)
        if not session:
            return
        api = session.get_api()
        if not api:
            return

        attachments = []

        # audios
        audios = list(record.audios.all())
        prepared_audios = prepare_audio_attachments(audios,
                                                    is_shuffle=group.is_audios_shuffle_enabled,
                                                    is_cut=config.CUT_ONE_AUDIO_ATTACHMENT
                                                    )

        attachments.extend(prepared_audios)

        # text
        record_text = delete_emoji_from_text(record.text) if not group.is_text_delete_enabled else ''

        artist_text = get_music_compilation_artist(audios)

        genre = get_music_compilation_genre(audios)
        if genre and genre['name'] is not 'banned':
            genre_text = genre['name']

            epithets = group.music_genre_epithets.all().order_by('id')
            if group.is_music_genre_epithet_enabled and epithets:
                epithet = find_next_element_by_last_used_id(epithets, group.last_used_music_genre_epithet_id)
                group.last_used_music_genre_epithet_id = epithet.id
                group.save(update_fields=['last_used_music_genre_epithet_id'])

                if genre['gender'] == 'М':
                    genre_text = f'{epithet.text_for_male} {genre_text}'
                elif genre['gender'] == 'Ж':
                    genre_text = f'{epithet.text_for_female} {genre_text}'
        else:
            genre_text = None

        if len(record_text) <= 50:
            text_to_image = record_text.replace('\n', ' ')
            record_text = ''
        else:
            text_to_image = ''

        if artist_text:
            text_to_image = f'{text_to_image}\n{artist_text}' if text_to_image else artist_text

        if genre_text:
            text_to_image = f'{text_to_image}\n{genre_text}' if text_to_image else genre_text

        # image
        image_file_paths = []
        record_original_image = record.images.first()
        abstractions = BackgroundAbstraction.objects.all().order_by('id')
        template_image = os.path.join(settings.BASE_DIR, 'posting/extras/image_templates', 'disc_template.png')

        if record_original_image:
            image_to_template = download_file(record_original_image.url)
            image_file_paths.append(image_to_template)
        elif abstractions or config.FORCE_USE_ABSTRACTION:
            abstraction = find_next_element_by_last_used_id(abstractions,
                                                            group.last_used_background_abstraction_id)
            group.last_used_background_abstraction_id = abstraction.id
            group.save(update_fields=['last_used_background_abstraction_id'])
            image_to_template = abstraction.picture
        else:
            record.set_failed()
            return

        result_image_name = paste_abstraction_on_template(template_image, image_to_template)
        image_file_paths.append(result_image_name)

        paste_text_on_music_image(result_image_name, text_to_image)

        attachments.extend(upload_photos(session, result_image_name, group_id))

        data_to_post = {
            'owner_id': f'-{group_id}',
            'from_group': 1,
            'message': record_text,
            'attachments': ','.join(attachments)
        }
        post_response = api.wall.post(**data_to_post)

        delete_files(image_file_paths)

        record.post_in_group_id = post_response.get('post_id', 0)
        record.post_in_group_date = timezone.now()
        record.group = group
        record.status = Record.POSTED
        record.save()
    except:
        log.error('got unexpected error in post music', exc_info=True)
        telegram.critical('Неожиданная ошибка при постинге музыки')
        record.set_failed()
    log.debug('post in group {} finished'.format(group_id))
