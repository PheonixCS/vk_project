#
import logging
import datetime

import vk_api
from celery import task

from posting.models import Group
from posting.poster import create_vk_api_using_login_password, fetch_group_id, upload_photo, upload_video


log = logging.getLogger('posting.scheduled')


@task
def examine_groups():
    log.debug('start group examination')
    groups_to_post_in = Group.objects.filter(user__isnull=False, donors__isnull=False)

    log.debug('got {} groups'.format(len(groups_to_post_in)))

    now_minute = datetime.datetime.now().minute

    for group in groups_to_post_in:
        log.debug('working with group {}'.format(group.id))

        api = create_vk_api_using_login_password(group.user.login, group.user.password, group.user.app_id)
        if not api:
            continue

        if not group.group_id:
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

            post_record.delay(api, group.id, record_with_max_rate)


@task
def post_record(api, group_id, record):
    log.debug('start posting in {} group'.format(group_id))
    try:
        attachments = list()

        videos = record.videos.all()
        if videos:
            for video in videos:
                attachments.append(upload_video(api, video.get_url(), group_id))

        images = record.images.all()
        if images:
            for image in images:
                attachments.append(upload_photo(api, image.url, group_id))

        api.wall.post(owner_id='-{}'.format(group_id),
                      from_group=1,
                      message=record.text,
                      attachments=','.join(attachments))
    except vk_api.VkApiError as error_msg:
        log.info('group {} got api error: {}'.format(group_id, error_msg))
        return False

    record.post_in_group_date = datetime.datetime.now()
    record.save(update_fields=['post_in_group_date'])
