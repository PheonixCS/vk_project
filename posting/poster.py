import datetime
import os

import vk_api
import requests
import logging
from PIL import Image

from posting.models import Group
from settings.models import Setting

log = logging.getLogger('posting.poster')

VK_API_VERSION = Setting.get_value(key='VK_API_VERSION')
PIXELS_TO_CUT_FROM_BOTTOM = Setting.get_value(key='PIXELS_TO_CUT_FROM_BOTTOM')


def create_vk_api_using_login_password(login, password, app_id):
    log.debug('create api called')
    vk_session = vk_api.VkApi(login=login, password=password, app_id=app_id)
    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        log.info('User {} got api error: {}'.format(login, error_msg))
        return None

    return vk_session.get_api()


def download_file(url):
    local_filename = url.split('/')[-1]
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    return local_filename


def upload_video(api, video_url, group_id):
    video_local_filename = download_file(video_url)
    upload = vk_api.VkUpload(api)
    video = upload.video(video_file=video_local_filename,
                         album_id='{}_00'.format(group_id),
                         group_id=int(group_id))
    if os.path.isfile(video_local_filename):
        os.remove(video_local_filename)
    return 'video{}_{}'.format(video[0]['owner_id'], video[0]['id'])


def crop_image(filepath):
    img = Image.open(filepath)
    width, height = img.size
    img.crop((0, 0, width, height - PIXELS_TO_CUT_FROM_BOTTOM)).save(filepath)


def upload_photo(api, photo_url, group_id):
    image_local_filename = download_file(photo_url)

    if '.gif' not in photo_url:
        crop_image(image_local_filename)

    upload = vk_api.VkUpload(api)
    photo = upload.photo(photos=image_local_filename,
                         album_id='{}_00'.format(group_id),
                         group_id=int(group_id))
    if os.path.isfile(image_local_filename):
        os.remove(image_local_filename)
    return 'photo{}_{}'.format(photo[0]['owner_id'], photo[0]['id'])


def post_record(api, group_id, record):
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

    return True


def fetch_group_id(api, domain_or_id):
    if domain_or_id.isdigit():
        return domain_or_id
    else:
        return api.utils.resolveScreenName(domain_or_id)['object_id']


def main():
    log.info('start main scrapper')
    groups_to_post_in = Group.objects.filter(user__isnull=False, donors__isnull=False)

    for group in groups_to_post_in:
        log.debug('working with group {}'.format(group.id))

        api = create_vk_api_using_login_password(group.user.login, group.user.password, group.user.app_id)
        if not api:
            continue

        if not group.group_id:
            group.group_id = fetch_group_id(api, group.domain_or_id)
            group.save(update_fields=['group_id'])

        if group.posting_time.minute == datetime.datetime.now().minute:
            records = [record for donor in group.donors.all() for record in
                       donor.records.filter(rate__isnull=False, post_in_group_date__isnull=True)]
            log.debug('got {} ready to post records'.format(len(records)))
            if not records:
                continue

            record_with_max_rate = max(records, key=lambda x:x.rate)
            log.debug('record {} got max rate'.format(record_with_max_rate))

            response = post_record(api, group.id, record_with_max_rate)

            if response:
                record_with_max_rate.post_in_group_date = datetime.datetime.now()
                record_with_max_rate.save(update_fields=['post_in_group_date'])


if __name__ == '__main__':
    main()
