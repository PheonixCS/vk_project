#
import os

import vk_api
import requests
import logging
from PIL import Image

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


def fetch_group_id(api, domain_or_id):
    if domain_or_id.isdigit():
        return domain_or_id
    else:
        return api.utils.resolveScreenName(domain_or_id)['object_id']
