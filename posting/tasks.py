import logging
import ast
import os
from datetime import datetime, timedelta
from random import choice, shuffle

import vk_api
from celery import shared_task
from constance import config
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone

from posting.core.horoscopes import generate_special_group_reference
from posting.core.horoscopes_images import transfer_horoscope_to_image
from posting.core.images import (
    is_all_images_not_horizontal,
    merge_poster_and_three_images,
    merge_six_images_into_one,
    is_text_on_image,
    paste_abstraction_on_template,
    paste_text_on_music_image
)
from posting.core.poster import (
    download_file,
    prepare_image_for_posting,
    delete_files,
    get_country_name_by_code,
    get_next_interval_by_movie_rating,
    get_movies_rating_intervals,
    find_next_element_by_last_used_id,
    get_music_compilation_genre,
    get_music_compilation_artist,
    find_suitable_record,
    filter_banned_records
)
from posting.core.text_utilities import replace_russian_with_english_letters, delete_hashtags_from_text, \
    delete_emoji_from_text
from posting.core.vk_helper import is_ads_posted_recently
from posting.models import Group, ServiceToken, AdRecord, BackgroundAbstraction
from scraping.core.horoscopes import fetch_zodiac_sign
from scraping.models import Record, Horoscope, Movie, Trailer
from services.vk.core import create_vk_session_using_login_password, create_vk_api_using_service_token, fetch_group_id
from services.vk.files import upload_video, upload_photo, check_docs_availability, check_video_availability
from services.vk.stat import get_group_week_statistics
from services.vk.wall import get_wall

log = logging.getLogger('posting.scheduled')


@shared_task(time_limit=59)
def examine_groups():
    log.debug('start group examination')
    groups_to_post_in = Group.objects.filter(
        user__isnull=False,
        is_posting_active=True
    ).distinct()

    log.debug('got {} groups'.format(len(groups_to_post_in)))

    now_time_utc = timezone.now()
    now_minute = now_time_utc.minute

    ads_time_threshold = now_time_utc - timedelta(hours=1, minutes=5)
    hour_ago_threshold = now_time_utc - timedelta(hours=1)
    allowed_time_threshold = now_time_utc - timedelta(hours=8)
    week_ago = now_time_utc - timedelta(days=7)
    today_start = now_time_utc.replace(hour=0, minute=0, second=0)

    for group in groups_to_post_in:
        log.debug('working with group {}'.format(group.domain_or_id))

        last_hour_ads = AdRecord.objects.filter(group=group, post_in_group_date__gt=ads_time_threshold)
        if last_hour_ads.exists():
            log.debug(f'got ads in last hour and 5 minutes for group {group.domain_or_id}. Skip.')
            continue

        if group.is_horoscopes and group.horoscopes.filter(post_in_group_date__isnull=True):
            # is_time_to_post = abs(now_minute - group.posting_time.minute) % config.HOROSCOPES_POSTING_INTERVAL == 0
            is_time_to_post = group.posting_time.minute == now_minute
        else:
            is_time_to_post = group.posting_time.minute == now_minute

        if group.is_movies:
            last_hour_posts = Movie.objects.filter(post_in_group_date__gt=hour_ago_threshold)
        elif group.is_horoscopes:
            last_hour_posts = Horoscope.objects.filter(group=group, post_in_group_date__gt=hour_ago_threshold)
        else:
            last_hour_posts = Record.objects.filter(group=group, post_in_group_date__gt=hour_ago_threshold)
        last_hour_posts_exist = last_hour_posts.exists()

        if last_hour_posts_exist and not is_time_to_post:
            log.info(f'got posts in last hour and 5 minutes for group {group.domain_or_id}')
            continue
        else:
            if not config.IS_DEV and is_ads_posted_recently(group):
                log.info(f'pass group {group.domain_or_id} because ad post was published recently')
                continue

        if not group.group_id:
            api = create_vk_session_using_login_password(group.user.login,
                                                         group.user.password,
                                                         group.user.app_id).get_api()
            if not api:
                continue
            group.group_id = fetch_group_id(api, group.domain_or_id)
            group.save(update_fields=['group_id'])

        movies_condition = (
                group.is_movies
                and (is_time_to_post or not last_hour_posts_exist or config.FORCE_MOVIE_POST)
        )
        if movies_condition:
            log.debug(f'{group.domain_or_id} in movies condition')

            posted_movies = Movie.objects.filter(post_in_group_date__isnull=False)
            if posted_movies:
                last_posted_movie = posted_movies.latest('post_in_group_date')
                last_movie_rating = last_posted_movie.rating
                log.debug(f'last posted movie id: {last_posted_movie.id or None}')
            else:
                log.warning('got no posted movies')
                last_movie_rating = None

            for _ in range(len(get_movies_rating_intervals())):
                next_rating_interval = get_next_interval_by_movie_rating(last_movie_rating)
                log.debug(f'next rating interval {next_rating_interval}')

                new_movie = Movie.objects.filter(trailers__status=Trailer.DOWNLOADED_STATUS,
                                                 rating__in=next_rating_interval,
                                                 post_in_group_date__isnull=True).last()
                if not new_movie:
                    log.debug('Got no new movie')
                    old_movie_threshold = now_time_utc - timedelta(days=config.OLD_MOVIES_TIME_THRESHOLD)
                    old_movies_ids = list(Movie.objects.filter(
                        trailers__vk_url__isnull=False,
                        post_in_group_date__lte=old_movie_threshold,
                        rating__in=next_rating_interval
                    ).values_list('id', flat=True))

                    try:
                        old_movie = choice(old_movies_ids)
                    except IndexError:
                        log.debug('old_movies_ids is empty')
                        old_movie = None

                    if not old_movie:
                        log.warning('Got no movies in last interval!')
                    else:
                        log.debug('Found old movie')
                        movie = old_movie
                        break
                else:
                    log.debug('Found new movie')
                    movie = new_movie.id
                    break

                last_movie_rating = next_rating_interval[0]

            else:
                movie = None

            if movie:
                post_movie.delay(group.group_id, movie)
            else:
                log.warning('got no movie')

        horoscope_condition = (
                group.is_horoscopes
                and is_time_to_post
                and group.horoscopes.filter(post_in_group_date__isnull=True)
        )
        if horoscope_condition:
            log.debug(f'{group.domain_or_id} in horoscopes condition')

            horoscope_records = group.horoscopes.filter(post_in_group_date__isnull=True)
            if horoscope_records.exists():
                horoscope_record = horoscope_records.last()
                post_horoscope.delay(group.user.login,
                                     group.user.password,
                                     group.user.app_id,
                                     group.group_id,
                                     horoscope_record.id
                                     )
                continue
            else:
                log.warning('got no horoscopes records')

        common_condition = (
                (is_time_to_post or not last_hour_posts_exist)
                and not group.is_movies
        )
        if common_condition:
            log.debug(f'{group.domain_or_id} in common condition')

            donors = group.donors.all()
            if not donors:
                log.warning(f'Group {group.domain_or_id} got no donors but in common condition!')
                continue

            if len(donors) > 1:
                # find last record id and its donor id
                last_record = Record.objects.filter(group=group).order_by('-post_in_group_date').first()
                if last_record:
                    donors = donors.exclude(pk=last_record.donor_id)

            records = Record.objects.filter(
                rate__isnull=False,
                status=Record.READY,
                post_in_group_date__isnull=True,
                failed_date__isnull=True,
                post_in_donor_date__gt=allowed_time_threshold,
                donor__in=donors
            )

            if group.banned_origin_attachment_types:
                records = filter_banned_records(records, group.banned_origin_attachment_types)

            log.debug('got {} ready to post records to group {}'.format(len(records), group.group_id))
            if not records:
                continue
            if config.POSTING_BASED_ON_SEX:

                if not group.sex_last_update_date or group.sex_last_update_date < week_ago:
                    sex_statistics_weekly.delay()
                    break

                if group.male_weekly_average_count == 0 or group.female_weekly_average_count == 0:
                    group_male_female_ratio = 1
                else:
                    group_male_female_ratio = group.male_weekly_average_count / group.female_weekly_average_count

                the_best_record = find_suitable_record(
                    records,
                    group_male_female_ratio,
                    config.RECORDS_SELECTION_PERCENT
                )
            else:
                the_best_record = max(records, key=lambda x: x.rate)

            the_best_record.status = Record.POSTING
            the_best_record.save(update_fields=['status'])
            log.debug('record {} got max rate for group {}'.format(the_best_record, group.group_id))

            try:
                if group.is_background_abstraction_enabled:
                    post_music.delay(group.user.login,
                                     group.user.password,
                                     group.user.app_id,
                                     group.group_id,
                                     the_best_record.id)
                else:
                    post_record.delay(group.user.login,
                                      group.user.password,
                                      group.user.app_id,
                                      group.group_id,
                                      the_best_record.id)
            except:
                log.error('got unexpected exception in examine_groups', exc_info=True)
                the_best_record.status = Record.FAILED
                the_best_record.save(update_fields=['status'])


@shared_task
def post_music(login, password, app_id, group_id, record_id):
    log.debug(f'start posting music in group {group_id}')

    group = Group.objects.get(group_id=group_id)
    record = Record.objects.get(pk=record_id)

    try:
        session = create_vk_session_using_login_password(login, password, app_id)
        api = session.get_api()
        audios = list(record.audios.all())

        attachments = []

        if group.is_audios_shuffle_enabled and len(audios) > 1:
            shuffle(audios)
            log.debug('group {} {} audios shuffled'.format(group_id, len(audios)))

        for audio in audios:
            attachments.append('audio{}_{}'.format(audio.owner_id, audio.audio_id))

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
        record_original_image = record.images.first()
        abstractions = BackgroundAbstraction.objects.all().order_by('id')

        if record_original_image:
            image_to_template = download_file(record_original_image.url)
        elif abstractions or config.FORCE_USE_ABSTRACTION:
            abstraction = find_next_element_by_last_used_id(abstractions,
                                                            group.last_used_background_abstraction_id)
            group.last_used_background_abstraction_id = abstraction.id
            group.save(update_fields=['last_used_background_abstraction_id'])
            image_to_template = abstraction.picture
        else:
            record.fail()
            return

        template_image = os.path.join(settings.BASE_DIR, 'posting/extras/image_templates', 'disc_template.png')
        result_image_name = paste_abstraction_on_template(template_image, image_to_template)
        paste_text_on_music_image(result_image_name, text_to_image)

        attachments.append(upload_photo(session, result_image_name, group_id))

        post_response = api.wall.post(owner_id=f'-{group_id}',
                                      from_group=1,
                                      message=record_text,
                                      attachments=','.join(attachments))

        record.post_in_group_id = post_response.get('post_id', 0)
        record.post_in_group_date = timezone.now()
        record.group = group
        record.status = Record.POSTED
        record.save()
    except:
        log.error('got unexpected error in post music', exc_info=True)
        record.fail()
    log.debug('post in group {} finished'.format(group_id))


@shared_task
def post_movie(group_id, movie_id):
    log.debug(f'start posting movies in {group_id} group')

    group = Group.objects.get(group_id=group_id)
    login = group.user.login
    password = group.user.password
    app_id = group.user.app_id

    session = create_vk_session_using_login_password(login, password, app_id)
    if not session:
        log.error(f'session not created in group {group_id}')
        return

    api = session.get_api()
    if not api:
        log.error(f'no api was created in group {group_id}')
        return

    movie = Movie.objects.get(pk=movie_id)

    attachments = []

    country_code = movie.production_country_code
    country = get_country_name_by_code(country_code) if country_code else ''

    trailer_name = f'{movie.title} ({movie.rating}&#11088;)'
    trailer_information = f'{movie.release_year}, ' \
        f'{country}{", " if country else ""}' \
        f'{", ".join(movie.genres.all().values_list("name", flat=True)[:2])}, ' \
        f'{str(timedelta(minutes=int(movie.runtime)))[:-3]}'

    video_description = f'{trailer_information}\n\n{movie.overview}'

    images = [frame.url for frame in movie.frames.all()]
    shuffle(images)
    images = images[:3]
    image_files = [download_file(image) for image in images]

    try:
        assert len(image_files) == 3
    except AssertionError:
        log.error('Number of images is not equal 3', exc_info=True)

    try:

        if config.ENABLE_MERGE_IMAGES_MOVIES:
            poster_file = download_file(movie.poster)
            poster_and_three_images = merge_poster_and_three_images(poster_file, image_files)
            delete_files(image_files)
            delete_files(poster_file)

            attachments.append(upload_photo(
                session,
                poster_and_three_images,
                group_id)
            )
            delete_files(poster_and_three_images)
        else:
            attachments.append(upload_photo(session, download_file(movie.poster), group_id))
            for image in image_files[:2]:
                attachments.append(upload_photo(session, image, group_id))
            delete_files(image_files)

        log.debug(f'movie {movie.title} post: got attachments {attachments}')

        uploaded_trailers = movie.trailers.filter(vk_url__isnull=False)
        downloaded_trailers = movie.trailers.filter(status=Trailer.DOWNLOADED_STATUS)

        if uploaded_trailers.exists():
            trailer = uploaded_trailers.first()
            uploaded_trailer = trailer.vk_url
        elif downloaded_trailers.exists():
            trailer = downloaded_trailers.first()
            uploaded_trailer = upload_video(session, trailer.file_path, group_id, trailer_name, video_description)

            if uploaded_trailer:
                delete_files(trailer.file_path)
                trailer.vk_url = uploaded_trailer
                trailer.status = Trailer.UPLOADED_STATUS
            else:
                log.warning('failed to upload trailer')
        else:
            log.error(f'movie {movie.title} got no trailer!')
            uploaded_trailer = None
            trailer = None

        if config.PUT_TRAILERS_TO_ATTACHMENTS and uploaded_trailer:
            attachments.append(uploaded_trailer)
            trailer_link = ''
        else:
            trailer_link = f'Трейлер: vk.com/{uploaded_trailer}'

        if uploaded_trailer and trailer:
            trailer.save(update_fields=['status', 'vk_url'])

        record_text = f'{trailer_name}\n\n' \
            f'{trailer_information}\n\n' \
            f'{trailer_link if uploaded_trailer else ""}\n\n' \
            f'{movie.overview}'

        post_response = api.wall.post(owner_id=f'-{group_id}',
                                      from_group=1,
                                      message=record_text,
                                      attachments=','.join(attachments))

        movie.post_in_group_date = timezone.now()
        movie.group = Group.objects.get(group_id=group_id)
        movie.save(update_fields=['post_in_group_date', 'group'])

        log.debug(f'{post_response} in group {group_id}')
    except:
        log.error('error in movie posting', exc_info=True)


@shared_task
def post_horoscope(login, password, app_id, group_id, horoscope_record_id):
    log.debug('start posting horoscopes in {} group'.format(group_id))

    session = create_vk_session_using_login_password(login, password, app_id)
    api = session.get_api()

    if not session:
        log.error('session not created in group {}'.format(group_id))
        return

    if not api:
        log.error('no api was created in group {}'.format(group_id))
        return

    group = Group.objects.get(group_id=group_id)
    horoscope_record = group.horoscopes.get(pk=horoscope_record_id)
    log.debug('{} horoscope record to post in {}'.format(horoscope_record.id, group.domain_or_id))

    try:
        attachments = []

        record_text = horoscope_record.text

        if config.HOROSCOPES_TO_IMAGE_ENABLED:
            horoscope_image_name = transfer_horoscope_to_image(record_text)
            attachments = upload_photo(session, horoscope_image_name, group_id)
            delete_files(horoscope_image_name)
            record_text = ''
        else:
            if group.is_replace_russian_with_english:
                record_text = replace_russian_with_english_letters(record_text)

            record_text = delete_hashtags_from_text(record_text)

            if horoscope_record.image_url and not config.HOROSCOPES_TO_IMAGE_ENABLED:
                image_local_filename = download_file(horoscope_record.image_url)
                attachments = upload_photo(session, image_local_filename, group_id)
                delete_files(image_local_filename)

        group_zodiac_sign = fetch_zodiac_sign(group.name)
        if not group_zodiac_sign:
            text_to_add = generate_special_group_reference(horoscope_record.text)
            record_text = '\n'.join([text_to_add, record_text]) if record_text else text_to_add

        post_response = api.wall.post(owner_id='-{}'.format(group_id),
                                      from_group=1,
                                      message=record_text,
                                      attachments=attachments)

        log.debug('{} in group {}'.format(post_response, group_id))
    except vk_api.VkApiError as error_msg:
        log.info('group {} got api error: {}'.format(group_id, error_msg))
        return
    except:
        log.error('caught unexpected exception in group {}'.format(group_id), exc_info=True)
        return

    horoscope_record.post_in_group_date = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    horoscope_record.save()
    log.debug('post horoscopes in group {} finished'.format(group_id))


@shared_task
def post_record(login, password, app_id, group_id, record_id):
    log.debug('start posting in {} group'.format(group_id))

    group = Group.objects.get(group_id=group_id)
    record = Record.objects.get(pk=record_id)

    try:
        session = create_vk_session_using_login_password(login, password, app_id)
        api = session.get_api()
    except:
        log.error('got unexpected exception in post_record for group {}'.format(group_id), exc_info=True)
        record.fail()
        return

    if not session:
        log.error('session not created in group {}'.format(group_id))
        record.fail()
        return

    if not api:
        log.error('no api was created in group {}'.format(group_id))
        record.fail()
        return

    try:
        attachments = []
        actions_to_unique_image = {}

        images = list(record.images.all())
        audios = list(record.audios.all())
        gifs = record.gifs.all()
        videos = record.videos.all()
        record_text = record.text

        record_text = delete_hashtags_from_text(record_text)

        text_to_image_condition = (len(images) == 1
                                   and group.is_text_filling_enabled
                                   and len(record_text) <= config.MAX_TEXT_TO_FILL_LENGTH)

        if group.is_text_delete_enabled:
            record_text = ''

        if text_to_image_condition:
            actions_to_unique_image['text_to_fill'] = delete_emoji_from_text(record_text)
            record_text = ''

        log.debug('got {} audios for group {}'.format(len(audios), group_id))

        if group.is_audios_shuffle_enabled and len(audios) > 1:
            shuffle(audios)
            log.debug('group {} {} audios shuffled'.format(group_id, len(audios)))

        for audio in audios:
            attachments.append('audio{}_{}'.format(audio.owner_id, audio.audio_id))

        # images part

        if group.is_replace_russian_with_english and not text_to_image_condition:
            record_text = replace_russian_with_english_letters(record_text)

        if group.is_merge_images_enabled:
            images = images[:6]

        log.debug('got {} images for group {}'.format(len(images), group_id))

        if group.is_photos_shuffle_enabled and len(images) > 1:
            shuffle(images)
            log.debug('group {} {} images shuffled'.format(group_id, len(images)))

        image_files = [download_file(image.url) for image in images[::-1]]

        if (
                group.is_merge_images_enabled
                and len(images) == 6
                and is_all_images_not_horizontal(image_files)
        ):
            old_image_files = image_files
            image_files = [merge_six_images_into_one(image_files)]
            delete_files(old_image_files)

        for image_local_filename in image_files:

            if group.is_image_mirror_enabled and not is_text_on_image(image_local_filename):
                actions_to_unique_image['mirror'] = True

            if group.RGB_image_tone:
                actions_to_unique_image['rgb_tone'] = group.RGB_image_tone

            percentage_to_crop_from_edges = config.PERCENTAGE_TO_CROP_FROM_EDGES
            if (
                    not group.is_merge_images_enabled
                    and group.is_changing_image_to_square_enabled
                    and not is_text_on_image(image_local_filename)
            ):
                actions_to_unique_image['crop_to_square'] = percentage_to_crop_from_edges

            prepare_image_for_posting(image_local_filename, **actions_to_unique_image)

            attachments.append(upload_photo(session, image_local_filename, group_id))

        delete_files(image_files)

        # gif part
        log.debug('got {} gifs for group {}'.format(len(gifs), group_id))
        if gifs and check_docs_availability(api, ['{}_{}'.format(gif.owner_id, gif.gif_id) for gif in gifs]):
            for gif in gifs:
                attachments.append('doc{}_{}'.format(gif.owner_id, gif.gif_id))
        elif gifs:
            record.fail()
            return

        log.debug('got {} videos in attachments for group {}'.format(len(videos), group_id))
        for video in videos:
            if check_video_availability(api, video.owner_id, video.video_id):
                attachments.append('video{}_{}'.format(video.owner_id, video.video_id))
            else:
                record.fail()
                return

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

        post_response = api.wall.post(owner_id='-{}'.format(group_id),
                                      from_group=1,
                                      message=record_text,
                                      attachments=','.join(attachments))
        log.debug('{} in group {}'.format(post_response, group_id))
    except vk_api.VkApiError as error_msg:
        log.info('group {} got api error: {}'.format(group_id, error_msg))
        record.fail()
        return
    except:
        log.error('caught unexpected exception in group {}'.format(group_id), exc_info=True)
        record.fail()
        return

    fields = ['post_in_group_id', 'post_in_group_date', 'group', 'status']

    record.post_in_group_id = post_response.get('post_id', 0)
    record.post_in_group_date = timezone.now()
    record.group = group
    record.status = Record.POSTED
    record.save(update_fields=fields)

    log.debug('post in group {} finished'.format(group_id))


@shared_task
def pin_best_post():
    """

    :return:
    """

    active_groups = Group.objects.filter(
        user__isnull=False,
        is_posting_active=True,
        is_pin_enabled=True).distinct()

    tokens = [token.app_service_token for token in ServiceToken.objects.all()]
    log.info('working with {} tokens: {}'.format(len(tokens), tokens))

    if not tokens:
        log.error('Got no tokens!')
        return

    for group in active_groups:
        token = choice(tokens)
        log.debug('work with token {}'.format(token))
        search_api = create_vk_api_using_service_token(token)
        time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=24)
        log.debug('search for posts from {} to now'.format(time_threshold))

        records_count = config.WALL_RECORD_COUNT_TO_PIN
        wall, error = get_wall(search_api, group.domain_or_id, count=records_count)
        records = [record for record in wall['items']
                   if datetime.fromtimestamp(record['date'], tz=timezone.utc) >= time_threshold]

        if records:
            log.debug('got {} wall records in last 24 hours'.format(len(records)))

            try:
                best = max(records, key=lambda item: item['likes']['count'])
            except KeyError:
                log.error('failed to fetch best record', exc_info=True)
                continue
            log.debug('got best record with id: {}'.format(best['id']))

            session = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id)
            api = session.get_api()

            group.group_id = fetch_group_id(api, group.domain_or_id)
            group.save(update_fields=['group_id'])

            try:
                response = api.wall.pin(owner_id='-{}'.format(group.group_id),
                                        post_id=best['id'])
                log.debug(response)
            except:
                log.error('failed to pin post', exc_info=True)
                continue

        else:
            log.warning('have no post in last 24 hours')
            continue


@shared_task
def delete_old_ads():
    log.info('delete_old_ads called')

    active_groups = Group.objects.filter(
        user__isnull=False,
        is_posting_active=True).distinct()

    for group in active_groups:

        hours = config.OLD_AD_RECORDS_HOURS
        time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=hours)

        ads = AdRecord.objects.filter(group=group, post_in_group_date__lt=time_threshold)
        log.debug('got {} ads in last 30 hours in group {}'.format(len(ads), group.group_id))

        if ads.exists():

            session = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id)
            if not session:
                continue

            api = session.get_api()
            if not api:
                continue

            ignore_ad_ids = []

            for ad in ads:
                try:
                    resp = api.wall.delete(owner_id='-{}'.format(group.group_id),
                                           post_id=ad.ad_record_id)
                    log.debug('delete_old_ads {} response: {}'.format(ad.ad_record_id, resp))
                except:
                    log.error('got unexpected error in delete_old_ads for {}'.format(ad.ad_record_id), exc_info=True)
                    ignore_ad_ids.append(ad.id)
                    continue

            ads = ads.exclude(pk__in=ignore_ad_ids)
            number_of_records, extended = ads.delete()
            log.debug('delete {} ads out of db'.format(number_of_records))

    log.info('finish deleting old ads')


@shared_task
def update_statistics():
    log.debug('update_statistics called')

    now_time = datetime.now(tz=timezone.utc)
    today_start = now_time.replace(hour=0, minute=0, second=0)
    yesterday_start = today_start - timedelta(hours=24)

    all_groups = Group.objects.all()
    all_group_ids = all_groups.values_list('domain_or_id', flat=True)
    log.debug('got {} groups in update_statistics'.format(len(all_group_ids)))

    token = ServiceToken.objects.filter().first().app_service_token
    log.debug('using {} token for update_statistics'.format(token))

    api = create_vk_api_using_service_token(token)

    if not api:
        log.error('cannot update statistics')

    try:
        response = api.groups.getById(group_ids=all_group_ids, fields=['members_count'])

        for piece in response:

            screen_name = piece.get('screen_name', None)
            members_count_now = piece.get('members_count', None)
            group_id = piece.get('id', None)

            try:
                group = all_groups.get(domain_or_id=group_id)
            except ObjectDoesNotExist:
                group = all_groups.get(domain_or_id=screen_name)

            if group:
                members_count_last = group.members_count or 0
                group.members_growth = members_count_now - members_count_last
                group.members_count = members_count_now

                starts = Q(post_in_group_date__gte=yesterday_start)
                ends = Q(post_in_group_date__lte=today_start)

                group.number_of_posts_yesterday = \
                    Record.objects.filter(group_id=group.domain_or_id).filter(starts & ends).count() + \
                    Horoscope.objects.filter(group_id=group.domain_or_id).filter(starts & ends).count() + \
                    Movie.objects.filter(group_id=group.domain_or_id).filter(starts & ends).count()

                group.number_of_ad_posts_yesterday = AdRecord.objects.filter(group_id=group.domain_or_id). \
                    filter(starts & ends).count()

                group.statistics_last_update_date = now_time.strftime('%Y-%m-%d %H:%M:%S')

                group.save(update_fields=['members_growth',
                                          'members_count',
                                          'number_of_posts_yesterday',
                                          'number_of_ad_posts_yesterday',
                                          'statistics_last_update_date'])

                log.debug('finish updating statistic for group {} {}'.format(group_id, screen_name))
            else:
                log.warning('problem with group {} {}'.format(group_id, screen_name))

    except:
        log.debug('got unexpected error in update_statistics', exc_info=True)
        return

    log.debug('update_statistics finished successfully')


@shared_task
def sex_statistics_weekly():
    log.debug('sex_statistics_weekly started')

    # TODO вынести в функцию и написать тесты
    try:
        groups_to_exclude = ast.literal_eval(config.EXCLUDE_GROUPS_FROM_SEX_STATISTICS_UPDATE)
    except SyntaxError:
        groups_to_exclude = []
        log.warning('sex_statistics_weekly got wrong format from config', exc_info=True)

    if groups_to_exclude:
        all_groups = Group.objects.exclude(group_id__in=groups_to_exclude)
    else:
        all_groups = Group.objects.all()
    log.debug('got {} groups in sex_statistics_weekly'.format(len(all_groups)))

    try:
        for group in all_groups:
            session = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id)
            if not session:
                continue

            api = session.get_api()
            if not api:
                continue

            stats = get_group_week_statistics(api, group_id=group.group_id)

            male_count_list = []
            female_count_list = []

            for day in stats:
                sex_list = day.get('sex', [])
                for sex in sex_list:
                    if sex.get('value', 'n') == 'f':
                        female_count_list.append(sex.get('visitors'))
                    elif sex.get('value', 'n') == 'm':
                        male_count_list.append(sex.get('visitors'))

            if male_count_list:
                male_average_count = sum(male_count_list) // len(male_count_list)
            else:
                male_average_count = 0

            if female_count_list:
                female_average_count = sum(female_count_list) // len(female_count_list)
            else:
                female_average_count = 0

            group.male_weekly_average_count = male_average_count
            group.female_weekly_average_count = female_average_count
            group.sex_last_update_date = timezone.now()

            group.save(
                update_fields=['male_weekly_average_count', 'female_weekly_average_count', 'sex_last_update_date'])
    except:
        log.debug('', exc_info=True)

    log.debug('sex_statistics_weekly finished')
