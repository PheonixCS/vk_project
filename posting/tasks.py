#
import logging
from datetime import datetime, timedelta
from random import choice

import vk_api
from celery import task
from django.utils import timezone

from posting.models import Group, ServiceToken
from scraping.models import Record
from posting.poster import (create_vk_session_using_login_password, fetch_group_id, upload_photo,
                            upload_gif, delete_hashtags_from_text)
from scraping.scraper import get_wall, create_vk_api_using_service_token


log = logging.getLogger('posting.scheduled')


@task
def examine_groups():
    log.debug('start group examination')
    groups_to_post_in = Group.objects.filter(user__isnull=False,
                                             donors__isnull=False,
                                             is_posting_active=True).distinct()

    log.debug('got {} groups'.format(len(groups_to_post_in)))

    now_minute = datetime.now().minute

    time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=1, minutes=5)
    allowed_time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=8)

    for group in groups_to_post_in:
        log.debug('working with group {}'.format(group.domain_or_id))

        if not group.group_id:
            api = create_vk_session_using_login_password(group.user.login, group.user.password,
                                                         group.user.app_id).get_api()
            if not api:
                continue
            group.group_id = fetch_group_id(api, group.domain_or_id)
            group.save(update_fields=['group_id'])

        log.debug('start searching for posted records since {}'.format(time_threshold))
        posts_in_last_hour_count = Record.objects.filter(group=group, post_in_group_date__gt=time_threshold).count()
        log.debug('got {} posts in last hour and 5 minutes'.format(posts_in_last_hour_count))

        if group.posting_time.minute == now_minute or posts_in_last_hour_count < 1:
            records = [record for donor in group.donors.all() for record in
                       donor.records.filter(rate__isnull=False,
                                            post_in_group_date__isnull=True,
                                            post_in_donor_date__gt=allowed_time_threshold)]
            log.debug('got {} ready to post records to group {}'.format(len(records), group.group_id))
            if not records:
                continue

            record_with_max_rate = max(records, key=lambda x: x.rate)
            log.debug('record {} got max rate for group {}'.format(record_with_max_rate, group.group_id))

            try:
                post_record.delay(group.user.login,
                                  group.user.password,
                                  group.user.app_id,
                                  group.group_id,
                                  record_with_max_rate.id)
            except:
                log.error('', exc_info=True)


@task
def post_record(login, password, app_id, group_id, record_id):
    log.debug('start posting in {} group'.format(group_id))

    # create api here coz celery through vk_api exception, idk why
    session = create_vk_session_using_login_password(login, password, app_id)
    api = session.get_api()

    try:
        group = Group.objects.get(group_id=group_id)
        record = Record.objects.get(pk=record_id)
    except:
        log.error('got unexpected exception in post_record for group {}'.format(group_id), exc_info=True)
        return

    if not session:
        log.error('session not created in group {}'.format(group_id))
        return

    if not api:
        log.error('no api was created in group {}'.format(group_id))
        return

    try:
        attachments = list()

        audios = record.audios.all()
        log.debug('got {} audios for group {}'.format(len(audios), group_id))
        for audio in audios:
            attachments.append('audio{}_{}'.format(audio.owner_id, audio.audio_id))

        images = record.images.all()
        log.debug('got {} images for group {}'.format(len(images), group_id))
        for image in images:
            attachments.append(upload_photo(session, image.url, group_id))

        gifs = record.gifs.all()
        log.debug('got {} gifs for group {}'.format(len(gifs), group_id))
        for gif in gifs:
            # attachments.append(upload_gif(session, gif.url))
            attachments.append('doc{}_{}'.format(gif.owner_id, gif.gif_id))

        videos = record.videos.all()
        log.debug('got {} videos in attachments for group {}'.format(len(videos), group_id))
        for video in videos:
            # uploaded_video_name = upload_video(session, api, video.get_url(), group_id)
            # if uploaded_video_name:
            #     attachments.append(uploaded_video_name)
            attachments.append('video{}_{}'.format(video.owner_id, video.video_id))

        post_response = api.wall.post(owner_id='-{}'.format(group_id),
                                      from_group=1,
                                      message=delete_hashtags_from_text(record.text),
                                      attachments=','.join(attachments))
        log.debug('{} in group {}'.format(post_response, group_id))
    except vk_api.VkApiError as error_msg:
        log.info('group {} got api error: {}'.format(group_id, error_msg))
        return
    except:
        log.error('caught unexpected exception in group {}'.format(group_id), exc_info=True)
        return

    record.post_in_group_date = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    record.group = group
    record.save(update_fields=['post_in_group_date', 'group'])
    log.debug('post in group {} finished'.format(group_id))


@task
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

        wall = [record for record in get_wall(search_api, group.domain_or_id, count=50)['items']
                if datetime.fromtimestamp(record['date'], tz=timezone.utc) >= time_threshold]

        if wall:
            log.debug('got {} wall records in last 24 hours'.format(len(wall)))

            try:
                best = max(wall, key=lambda item: item['likes']['count'])
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
