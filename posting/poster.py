import logging
import os
import re
from datetime import datetime, timedelta
from math import ceil
from textwrap import wrap

import cv2
import numpy as np
import requests
import vk_api
from PIL import Image, ImageFont, ImageDraw
from constance import config
from django.conf import settings
from django.utils import timezone

from posting.transforms import RGBTransform
from scraping.core.vk_helper import get_wall

log = logging.getLogger('posting.poster')


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


def crop_image(filepath, box):
    # box = (x coordinate to start croping, y coordinate to start croping, width to crop, height to crop)
    log.debug('crop_image called')
    img = Image.open(os.path.join(settings.BASE_DIR, filepath))
    try:
        image = img.crop(box)
        if filepath.endswith('.jpg'):
            image.save(filepath, 'JPEG', quality=95, progressive=True)
        else:
            image.save(filepath)
    except ValueError:
        log.debug('image not cropped!')
        os.remove(filepath)
        return False
    log.debug('image {} cropped'.format(filepath))
    return True


def crop_percentage_from_image_edges(filepath, percentage_to_crop):
    log.debug('crop_percentage_from_image_edges for {} called'.format(filepath))
    img = Image.open(os.path.join(settings.BASE_DIR, filepath))
    width, height = img.size
    log.debug('image {} width: {}, height: {}'.format(filepath, width, height))
    if width > height:
        pixels_to_crop = width * percentage_to_crop
        log.debug('pixels to crop from left and right: {}'.format(pixels_to_crop))
        crop_image(filepath, (pixels_to_crop, 0, width - pixels_to_crop, height))
    elif height > width:
        pixels_to_crop = height * percentage_to_crop
        log.debug('pixels to crop from top and bottom: {}'.format(pixels_to_crop))
        crop_image(filepath, (0, pixels_to_crop, width, height - pixels_to_crop))
    else:
        log.debug('image {} is square'.format(filepath))


def color_image_in_tone(filepath, red_tone, green_tone, blue_tone, factor):
    log.debug('color_image_in_tone called')
    img = Image.open(os.path.join(settings.BASE_DIR, filepath))
    img = img.convert('RGB')
    try:
        RGBTransform().mix_with((red_tone, green_tone, blue_tone), factor=factor / 100).applied_to(img).save(filepath)
    except:
        log.debug('image not toned!')
        os.remove(filepath)
        return False
    log.debug(
        'image {} colored in tone {} {} {} and factor {}'.format(filepath, red_tone, green_tone, blue_tone, factor))
    return True


def expand_image_with_white_color(filepath, pixels):
    log.debug('expand_image_with_white_color called')
    white_color = (255, 255, 255)

    old_image = Image.open(os.path.join(settings.BASE_DIR, filepath))
    new_image = Image.new('RGB', (old_image.width, old_image.height + pixels), white_color)

    new_image.paste(old_image, (0, pixels))

    if filepath.endswith('.jpg'):
        new_image.save(filepath, 'JPEG', quality=95, progressive=True)
    else:
        new_image.save(filepath)
    log.debug('expand_image_with_white_color finished')

    return filepath


def is_text_fit_to_width(text, width_in_chars, width_in_pixels, font_object):
    for line in wrap(text, width_in_chars):
        if font_object.getsize(line)[0] > width_in_pixels:
            return False
    return True


def calculate_max_len_in_chars(text, width_in_pixels, font_object):
    log.debug('calculate_max_len_in_chars called')

    max_width_in_chars = len(text)
    temp_text = wrap(text, max_width_in_chars)

    while max_width_in_chars and not is_text_fit_to_width(temp_text, max_width_in_chars, width_in_pixels, font_object):
        max_width_in_chars -= 1
        temp_text = wrap(text, max_width_in_chars)

    log.debug('max_width_in_chars = {}'.format(max_width_in_chars))
    return max_width_in_chars


def fil_image_with_text(filepath, text, percent=config.FONT_SIZE_PERCENT, font_name=config.FONT_NAME):
    log.debug('fil_image_with_text called')
    if not text:
        log.debug('got no text in fil_image_with_text')
        return

    black_color = (0, 0, 0)

    with Image.open(os.path.join(settings.BASE_DIR, filepath)) as temp:
        image_width, image_height = temp.width, temp.height

    # size in pixels
    size = ceil(image_height * percent / 100)

    font = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'posting/extras/fonts', font_name), size)

    if not is_text_fit_to_width(text, len(text), image_width - 10, font):
        text_max_width_in_chars = calculate_max_len_in_chars(text, image_width, font)
        text = '\n'.join(wrap(text, text_max_width_in_chars))

    offset = (text.count('\n') + 1) * (size + 15)

    if text.count('\n') == 0:
        # center text
        text_width = font.getsize(text)[0]
        text_height = font.getsize(text)[1]
        x, y = (image_width - text_width) // 2, (offset - text_height) // 2
    else:
        x, y = 5, 1

    log.debug('offset = {}, size = {}, x, y = [{},{}]'.format(offset, size, x, y))

    filepath = expand_image_with_white_color(filepath, offset)

    image = Image.open(filepath)
    draw = ImageDraw.Draw(image)

    # TODO make multi line custom function
    draw.multiline_text((x, y), text, black_color, font=font)

    if filepath.endswith('.jpg'):
        image.save(filepath, 'JPEG', quality=95, progressive=True)
    else:
        image.save(filepath)
    log.debug('fil_image_with_text finished')


def is_all_images_of_same_size(files):
    image_sizes = [Image.open(os.path.join(settings.BASE_DIR, image)).size for image in files]
    return image_sizes[1:] == image_sizes[:-1]


def merge_six_images_into_one(files):
    log.debug('merge_six_images_into_one called')
    img = Image.open(os.path.join(settings.BASE_DIR, files[0]))
    width, height = img.size

    result = Image.new("RGB", (width * 3, height * 2))

    for index, file in enumerate(files):
        log.debug('start work with image {}'.format(file))
        img = Image.open(os.path.join(settings.BASE_DIR, file))

        x = index // 2 * width
        y = index % 2 * height
        result.paste(img, (x, y, x + width, y + height))

        log.debug('image {} deleted'.format(file))
        os.remove(file)

    result.save(files[0])

    log.debug('merge_six_images_into_one finished')
    return files[0]


def is_text_on_image(filepath):
    log.debug('is_text_on_image {} called'.format(filepath))
    large = cv2.imread(os.path.join(settings.BASE_DIR, filepath))
    rgb = cv2.pyrDown(large)
    small = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    grad = cv2.morphologyEx(small, cv2.MORPH_GRADIENT, kernel)

    _, bw = cv2.threshold(grad, 0.0, 255.0, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
    connected = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel)
    im2, contours, hierarchy = cv2.findContours(connected.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    mask = np.zeros(bw.shape, dtype=np.uint8)

    for idx in range(len(contours)):
        x, y, w, h = cv2.boundingRect(contours[idx])
        mask[y:y + h, x:x + w] = 0
        cv2.drawContours(mask, contours, idx, (255, 255, 255), -1)
        r = float(cv2.countNonZero(mask[y:y + h, x:x + w])) / (w * h)

        if r > config.CV_RATIO and w > config.CV_WIDTH and h > config.CV_HEIGHT:
            log.debug('found text on image {}'.format(filepath))
            return True

    log.debug('no text found on image {}'.format(filepath))
    return False


def mirror_image(filepath):
    log.debug('mirror image {} called'.format(filepath))
    img = Image.open(os.path.join(settings.BASE_DIR, filepath))
    try:
        mirrored_image = img.transpose(Image.FLIP_LEFT_RIGHT)
        if filepath.endswith('.jpg'):
            mirrored_image.save(filepath, 'JPEG', quality=95, progressive=True)
        else:
            mirrored_image.save(filepath)
    except ValueError:
        log.debug('image not mirrored!')
        os.remove(filepath)
        return False
    log.debug('image {} mirrored'.format(filepath))
    return True


def prepare_image_for_posting(image_local_filepath, **kwargs):
    keys = kwargs.keys()

    if 'mirror' in keys:
        mirror_image(image_local_filepath)

    if 'crop_to_square' in keys:
        crop_percentage_from_image_edges(image_local_filepath, kwargs.get('crop_to_square'))

    if 'rgb_tone' in keys:
        red_tone, green_tone, blue_tone, factor = list(map(int, kwargs.get('rgb_tone').split()))
        color_image_in_tone(image_local_filepath, red_tone, green_tone, blue_tone, factor)

    if 'text_to_fill' in keys:
        fil_image_with_text(image_local_filepath, kwargs.get('text_to_fill'))


def upload_photo(session, image_local_filepath, group_id):
    log.debug('upload_photo called')

    try:
        upload = vk_api.VkUpload(session)
        photo = upload.photo_wall(photos=image_local_filepath,
                                  group_id=int(group_id))
    except:
        log.error('exception while uploading photo', exc_info=True)
        return

    if os.path.isfile(image_local_filepath):
        os.remove(image_local_filepath)

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


def delete_double_spaces_from_text(text):
    text = re.sub(' +', ' ', text)
    return text


def delete_hashtags_from_text(text):
    # link hashtag looks like '#hello@user', common looks like '#hello'
    text_without_link_hashtags = re.sub(r'(@\w*)', '', text)
    text_without_double_spaces = delete_double_spaces_from_text(text_without_link_hashtags)
    return text_without_double_spaces


def delete_emoji_from_text(text):
    log.debug('delete_emoji_from_text called. Text: "{}"'.format(text))
    # text_without_emoji = re.sub(u'[\u0000-\u052F]+', ' ', text)
    last_char_code = 1279  # 04FF
    text_without_emoji = ''.join(letter for letter in text if ord(letter) <= last_char_code)
    log.debug('text after deleting "{}"'.format(text_without_emoji))
    text_without_double_spaces = delete_double_spaces_from_text(text_without_emoji)
    return text_without_double_spaces


def get_ad_in_last_hour(api, group_id):
    log.debug('get_ad_in_last_hour called')
    time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=1)

    try:
        wall = [record for record in get_wall(api, group_id)['items']
                if record.get('marked_as_ads', False) and
                datetime.fromtimestamp(record['date'], tz=timezone.utc) >= time_threshold]

        if wall and wall[0].get('id', None) and wall[0].get('date', None):
            ad = {'id': wall[0].get('id'),
                  'date': wall[0].get('date')}
            log.debug('got ad with id {} in group {}'.format(ad['id'], group_id))
            return ad
    except:
        log.error('got unexpected error in get_ad_in_last_hour', exc_info=True)


def check_docs_availability(api, docs):
    """

    :param docs: list of dictionaries
    :type docs: list
    :return: true if all docs are available
    :rtype: bool
    """
    log.debug('check_docs_availability called')

    try:
        resp = api.docs.getById(docs=','.join(docs))

        if len(resp) == len(docs):
            return True
        else:
            log.info('check_docs_availability failed')
            return False

    except:
        log.error('got unexpected error in check_docs_availability', exc_info=True)


def check_video_availability(api, owner_id, video_id):
    """

    :param api: api object
    :param video_id: video id from vk
    :param owner_id: string  representing video owner in vk way
    :return: true if video available
    """

    log.debug('check_video_availability called')

    try:
        resp = api.video.get(owner_id=owner_id, videos='{}_{}'.format(owner_id, video_id))

        if resp.get('items'):
            return True
        else:
            log.info('check_video_availability failed')
            return False

    except:
        log.error('got unexpected error in check_video_availability', exc_info=True)
