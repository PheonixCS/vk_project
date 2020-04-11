import logging
from datetime import timedelta
from random import shuffle

from celery import shared_task
from constance import config
from django.utils import timezone

from posting.core.images import merge_poster_and_three_images
from posting.core.poster import get_country_name_by_code
from posting.core.files import download_file, delete_files
from posting.models import Group
from scraping.models import Movie, Trailer
from services.vk.core import create_vk_session_using_login_password
from services.vk.files import upload_photos, upload_video

log = logging.getLogger('posting.scheduled')
telegram = logging.getLogger('telegram')


@shared_task(time_limit=60)
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
            delete_files(poster_file)

            attachments.extend(upload_photos(session, poster_and_three_images, group_id))

            delete_files(poster_and_three_images)
        else:
            movie_poster = download_file(movie.poster)

            to_upload = [movie_poster]
            to_upload.extend(image_files[:2])

            attachments.extend(upload_photos(session, to_upload, group_id))

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
        telegram.critical('Неожиданная ошибка при постинге фильмов')
