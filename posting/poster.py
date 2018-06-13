#
import logging
import os
import re
from datetime import datetime, timedelta

import requests
import vk_api
from PIL import Image
from django.utils import timezone

from scraping.scraper import get_wall
from settings.models import Setting

log = logging.getLogger('posting.poster')

VK_API_VERSION = Setting.get_value(key='VK_API_VERSION')
PIXELS_TO_CUT_FROM_BOTTOM = Setting.get_value(key='PIXELS_TO_CUT_FROM_BOTTOM')


def create_vk_session_using_login_password(login, password, app_id):
    log.debug('create api called')
    vk_session = vk_api.VkApi(login=login, password=password, app_id=app_id)
    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        log.info('User {} got api error: {}'.format(login, error_msg))
        return None
    except:
        log.error('got unexpected error in create_vk_session_using_login_password', exc_info=True)

    return vk_session


def download_file(url, extension=None):
    log.debug('download_file called')
    local_filename = url.split('/')[-1]
    if extension:
        local_filename += '.{}'.format(extension)

    r = requests.get(url)
    with open(local_filename, 'wb') as f:
        f.write(r.content)

    log.debug('{} file downloaded'.format(local_filename))
    return local_filename


def upload_video(session, api, video_url, group_id):
    log.debug('upload_video called')

    try:
        video = api.video.get(videos=video_url)
    except:
        log.error('exception while getting video', exc_info=True)
        return

    files = video['items'][0]
    key_of_max_size_photo = max([key for key in files], key=lambda x: int(x.split('_')[1]))
    video_local_filename = download_file(files[key_of_max_size_photo], key_of_max_size_photo.split('_')[0])

    try:
        upload = vk_api.VkUpload(session)
        video = upload.video(video_file=video_local_filename,
                             group_id=int(group_id))
    except:
        log.error('exception while uploading video', exc_info=True)
        return

    if os.path.isfile(video_local_filename):
        os.remove(video_local_filename)

    return 'video{}_{}'.format(video[0]['owner_id'], video[0]['id'])


def upload_gif(session, gif_url):
    log.debug('upload_gif called')
    gif_local_filename = download_file(gif_url, 'gif')

    try:
        upload = vk_api.VkUpload(session)
        gif = upload.document(doc=gif_local_filename)
    except:
        log.error('exception while uploading gif', exc_info=True)
        return

    if os.path.isfile(gif_local_filename):
        os.remove(gif_local_filename)

    return 'doc{}_{}'.format(gif[0]['owner_id'], gif[0]['id'])


def crop_image(filepath):
    log.debug('crop_image called')
    img = Image.open(filepath)
    width, height = img.size
    try:
        img.crop((0, 0, width, height - PIXELS_TO_CUT_FROM_BOTTOM)).save(filepath)
    except ValueError:
        log.debug('image not cropped!')
        os.remove(filepath)
        return False
    log.debug('image {} cropped'.format(filepath))
    return True


def upload_photo(session, photo_url, group_id):
    log.debug('upload_photo called')
    image_local_filename = download_file(photo_url)

    crop_image(image_local_filename)

    try:
        upload = vk_api.VkUpload(session)
        photo = upload.photo_wall(photos=image_local_filename,
                                  group_id=int(group_id))
    except:
        log.error('exception while uploading photo', exc_info=True)
        return

    if os.path.isfile(image_local_filename):
        os.remove(image_local_filename)

    return 'photo{}_{}'.format(photo[0]['owner_id'], photo[0]['id'])


def fetch_group_id(api, domain_or_id):
    log.debug('fetch_group_id called for group {}'.format(domain_or_id))
    if domain_or_id.isdigit():
        group_id = domain_or_id
    else:
        try:
            group_id = api.utils.resolveScreenName(domain_or_id)['object_id']
        except:
            log.error('got exception while fetching group id', exc_info=True)
            return
    return group_id


def delete_hashtags_from_text(text):
    # link hashtag looks like '#hello@user', common looks like '#hello'
    text_without_link_hashtags = re.sub('(@\w*)', '', text)
    text_without_double_spaces = re.sub(' +', ' ', text_without_link_hashtags)
    return text_without_double_spaces


def get_ad_in_last_hour(api, group_id):
    log.debug('get_ad_in_last_hour called')
    time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=1)

    try:
        wall = [record for record in get_wall(api, group_id)['items']
                if datetime.fromtimestamp(record['date'], tz=timezone.utc and
                                          record.get('marked_as_ads', False)) >= time_threshold]

        if wall and wall[0].get('id', None) and wall[0].get('date', None):
            ad = {'id': wall[0].get('id'),
                  'date': wall[0].get('date')}
            log.debug('got ad with id {} in group {}'.format(ad['id'], group_id))
            return ad
    except:
        log.error('got unexpected error in get_ad_in_last_hour', exc_info=True)
