#
import logging
import datetime

import vk_api
from celery import task

from posting.models import Group
from scraping.models import Record
from posting.poster import create_vk_session_using_login_password, fetch_group_id, upload_photo, upload_video, \
    upload_gif, delete_hashtags_from_text

log = logging.getLogger('posting.scheduled')


@task
def examine_groups():
    log.debug('start group examination')
    groups_to_post_in = Group.objects.filter(user__isnull=False,
                                             donors__isnull=False,
                                             is_posting_active=True).distinct()

    log.debug('got {} groups'.format(len(groups_to_post_in)))

    now_minute = datetime.datetime.now().minute

    for group in groups_to_post_in:
        log.debug('working with group {}'.format(group.domain_or_id))

        if not group.group_id:
            api = create_vk_session_using_login_password(group.user.login, group.user.password,
                                                         group.user.app_id).get_api()
            if not api:
                continue
            group.group_id = fetch_group_id(api, group.domain_or_id)
            group.save(update_fields=['group_id'])

        if group.posting_time.minute == now_minute:
            records = [record for donor in group.donors.all() for record in
                       donor.records.filter(rate__isnull=False, post_in_group_date__isnull=True)]
            log.debug('got {} ready to post records'.format(len(records)))
            if not records:
                continue

            record_with_max_rate = max(records, key=lambda x: x.rate)
            log.debug('record {} got max rate'.format(record_with_max_rate))

            try:
                post_record.delay(group.user.login,
                                  group.user.password,
                                  group.user.app_id,
                                  group.group_id,
                                  record_with_max_rate.record_id)
            except:
                log.error('', exc_info=True)


@task
def post_record(login, password, app_id, group_id, record_id):
    log.debug('start posting in {} group'.format(group_id))

    # create api here coz celery through vk_api exception, idk why
    session = create_vk_session_using_login_password(login, password, app_id)
    api = session.get_api()

    record = Record.objects.get(record_id=record_id)

    if not session:
        log.error('session not created')
        return
    # record = Record.objects.get(record_id=record_id)

    try:
        attachments = list()

        videos = record.videos.all()
        log.debug('got {} videos in attachments'.format(len(videos)))
        for video in videos:
            # uploaded_video_name = upload_video(session, api, video.get_url(), group_id)
            # if uploaded_video_name:
            #     attachments.append(uploaded_video_name)
            attachments.append('video{}_{}'.format(video.owner_id, video.video_id))

        images = record.images.all()
        log.debug('got {} images'.format(len(images)))
        for image in images:
            attachments.append(upload_photo(session, image.url, group_id))

        gifs = record.gifs.all()
        log.debug('got {} gifs'.format(len(gifs)))
        for gif in gifs:
            attachments.append(upload_gif(session, gif.url))

        post_response = api.wall.post(owner_id='-{}'.format(group_id),
                                      from_group=1,
                                      message=delete_hashtags_from_text(record.text),
                                      attachments=','.join(attachments))
        log.debug('{}'.format(post_response))
    except vk_api.VkApiError as error_msg:
        log.info('group {} got api error: {}'.format(group_id, error_msg))
        return
    except:
        log.error('caught exception', exc_info=True)
        return

    record.post_in_group_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    record.save(update_fields=['post_in_group_date'])
