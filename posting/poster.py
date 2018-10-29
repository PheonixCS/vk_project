import logging
import os
import re
from datetime import datetime, timedelta
from math import ceil
from textwrap import wrap

import pytesseract
import requests
import vk_api
from PIL import Image, ImageFont, ImageDraw
from constance import config
from django.conf import settings
from django.utils import timezone

from posting.extras.transforms import RGBTransform
from scraping.core.vk_helper import get_wall

log = logging.getLogger('posting.poster')


def create_vk_session_using_login_password(login, password, app_id):
    log.debug('create api called')
    vk_session = vk_api.VkApi(login=login, password=password, app_id=app_id, api_version=config.VK_API_VERSION)
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


def delete_files(file_paths):
    log.debug('delete_files called with {} files'.format(len(file_paths)))

    if isinstance(file_paths, list):
        for file in file_paths:
            try:
                os.remove(file)
            except FileNotFoundError as exc:
                log.error('Fail to delete file {}'.format(exc))
                continue
    elif isinstance(file_paths, str):
        try:
            os.remove(file_paths)
        except FileNotFoundError as exc:
            log.error('Fail to delete file {}'.format(exc))
    else:
        log.warning('delete_files got wrong type')
        return
    log.debug('delete_files finished')


def upload_video(session, video_local_filename, group_id, name, description):
    log.debug('upload_video called')

    try:
        upload = vk_api.VkUpload(session)
        video = upload.video(video_file=video_local_filename,
                             group_id=int(group_id),
                             name=name,
                             description=description,
                             no_comments=True)
    except:
        log.error('exception while uploading video', exc_info=True)
        return

    return 'video{}_{}'.format(video['owner_id'], video['video_id'])


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
    """

    :param text: text as string
    :param width_in_chars:
    :param width_in_pixels:
    :param font_object:
    :return:

    :type text: str
    """
    for line in wrap(text, width_in_chars):
        if font_object.getsize(line)[0] > width_in_pixels:
            return False
    return True


def calculate_max_len_in_chars(text, width_in_pixels, font_object):
    log.debug('calculate_max_len_in_chars called')

    max_width_in_chars = len(text)
    temp_text = wrap(text, max_width_in_chars)

    while (
        max_width_in_chars
        and not is_text_fit_to_width(' '.join(temp_text), max_width_in_chars, width_in_pixels, font_object)
    ):
        max_width_in_chars -= 1
        temp_text = wrap(text, max_width_in_chars)

    log.debug('max_width_in_chars = {}'.format(max_width_in_chars))
    return max_width_in_chars


def fill_image_with_text(filepath, text, percent=config.FONT_SIZE_PERCENT, font_name=config.FONT_NAME):
    log.debug('fill_image_with_text called')
    if not text:
        log.debug('got no text in fill_image_with_text')
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
    log.debug('fill_image_with_text finished')


def divergence(one, two):
    return abs(one-two)/max(one, two)


def is_images_size_nearly_the_same(files, max_divergence):
    # FIXME #refactor too much file openings
    images_sizes = [Image.open(os.path.join(settings.BASE_DIR, image)).size for image in files]

    width = [size[0] for size in images_sizes]
    height = [size[1] for size in images_sizes]

    divergence_width = divergence(max(width), min(width))
    divergence_height = divergence(max(height), min(height))

    log.debug('max divergence = {}, divergence width = {}, divergence height = {}'.format(
        max_divergence,
        divergence_width,
        divergence_height
    ))

    return divergence_width <= max_divergence and divergence_height <= max_divergence


def is_all_images_not_horizontal(files):
    images_sizes = [Image.open(os.path.join(settings.BASE_DIR, image)).size for image in files]

    width = [size[0] for size in images_sizes]
    height = [size[1] for size in images_sizes]

    return all(height >= width for width, height in zip(width, height))


def get_smallest_image_size(sizes):
    min_size = min(sizes, key=lambda size: size[0]*size[1])
    return min_size


def calculate_size_from_one_side(origin_width, origin_height, width=None, height=None):
    r_width, r_height = origin_width, origin_height

    if width:
        r_width, r_height = int(width), int(width/origin_width*origin_height)

    if height:
        r_width, r_height = int(origin_width/origin_height*height), int(height)

    log.debug('calculate_size_from_one_side finished with sizes orig - {}:{}, new - {}:{}'.format(
        origin_width, origin_height, r_width, r_height
    ))

    return r_width, r_height


def resize_image_aspect_ratio_by_two_sides(image_object, width, height):
    log.debug('resize_image_aspect_ratio_by_two_sides called with {}:{}'.format(width, height))

    orig_width = image_object.size[0]
    orig_height = image_object.size[1]

    if orig_width/orig_height >= width/height:
        new_size = calculate_size_from_one_side(orig_width, orig_height, height=height)
    else:
        new_size = calculate_size_from_one_side(orig_width, orig_height, width=width)

    return image_object.resize(new_size, Image.ANTIALIAS)


def resize_image_aspect_ratio_by_one_side(image_object, width=None, height=None):
    log.debug('resize_image_aspect_ratio_by_two_sides called with {}:{}'.format(width, height))

    new_size = calculate_size_from_one_side(image_object.size[0], image_object.size[1], width, height)

    return image_object.resize(new_size)


def merge_poster_and_three_images(poster, images):
    log.debug('merge_poster_and_three_images called')

    offset = config.SIX_IMAGES_OFFSET
    filepath = f'temp_{poster}'

    images_sizes = [Image.open(os.path.join(settings.BASE_DIR, image)).size for image in images]
    poster_width, poster_height = Image.open(os.path.join(settings.BASE_DIR, poster)).size
    print(poster_width, poster_height)

    poster_image_object = Image.open(os.path.join(settings.BASE_DIR, poster))

    required_width = min([size[0] for size in images_sizes])
    required_height = min([size[1] for size in images_sizes])

    height = required_height * 3 + offset * 2

    poster_width, poster_height = calculate_size_from_one_side(poster_width, poster_height, height=height)

    width = poster_width + offset + required_width

    print(width, height, poster_width, poster_height)

    result = Image.new('RGB', (width, height), 'White')
    poster_image_object = resize_image_aspect_ratio_by_two_sides(poster_image_object, width=poster_width, height=height)
    cropped = poster_image_object.crop((0, 0, poster_width, poster_height))
    result.paste(cropped)

    for index, image in enumerate(images):
        x = poster_width + offset
        y = index*(required_height + offset)

        img_object = Image.open(os.path.join(settings.BASE_DIR, image))
        img_object = resize_image_aspect_ratio_by_two_sides(img_object, width=required_width, height=required_height)

        cropped = img_object.crop((0, 0, required_width, required_height))
        result.paste(cropped, (x, y, x + required_width, y + required_height))

    result.save(filepath, 'JPEG', quality=95, progressive=True)
    log.debug('merge_poster_and_three_images finished')
    return filepath


def merge_six_images_into_one(files):
    log.debug('merge_six_images_into_one called')

    offset = config.SIX_IMAGES_OFFSET
    filepath = 'temp_{}'.format(files[0])

    # FIXME #refactor too much file openings
    images_sizes = [Image.open(os.path.join(settings.BASE_DIR, image)).size for image in files]
    min_width, min_height = get_smallest_image_size(images_sizes)

    result = Image.new('RGB', (min_width * 3 + offset*2, min_height * 2 + offset), 'White')

    for index, img_file_name in enumerate(files):

        x = index % 3 * (min_width + offset)
        y = index // 3 * (min_height + offset)

        img = Image.open(os.path.join(settings.BASE_DIR, img_file_name))
        img = resize_image_aspect_ratio_by_two_sides(img, width=min_width, height=min_height)

        cropped = img.crop((0, 0, min_width, min_height))
        result.paste(cropped, (x, y, x + min_width, y + min_height))

    result = resize_image_aspect_ratio_by_one_side(result, width=config.SIX_IMAGES_WIDTH)
    result.save(filepath, 'JPEG', quality=95, progressive=True)

    log.debug('merge_six_images_into_one finished')
    return filepath


def is_text_on_image(filepath):
    log.debug('is_text_on_image {} called'.format(filepath))

    try:
        rus_text = pytesseract.image_to_string(Image.open(filepath), lang='rus')
        eng_text = pytesseract.image_to_string(Image.open(filepath), lang='eng')
    except:
        log.error('error in is_text_on_image', exc_info=True)
        return True

    if rus_text or eng_text:
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
        fill_image_with_text(image_local_filepath, kwargs.get('text_to_fill'))


def upload_photo(session, image_local_filepath, group_id):
    log.debug('upload_photo called')

    try:
        upload = vk_api.VkUpload(session)
        photo = upload.photo_wall(photos=image_local_filepath,
                                  group_id=int(group_id))
    except:
        log.error('exception while uploading photo', exc_info=True)
        return

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


def get_group_week_statistics(api, group_id):

    now = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d')
    week_ago = (datetime.now(tz=timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')

    print(now, week_ago)

    return api.stats.get(group_id=group_id, date_from=week_ago, date_to=now)


def find_the_best_post(records, best_ratio, percent=20):
    log.debug('find_the_best_post called')

    eps = 0.1
    records.sort(key=lambda x: x.rate, reverse=True)

    if len(records) > 10:
        records = records[:int(len(records) / 100 * percent)]

    for i in range(1, 6):
        exact_ratio_records = [record for record in records if
                               0 <= abs(record.males_females_ratio-best_ratio) <= i*eps]

        if exact_ratio_records:
            best_record = max(exact_ratio_records, key=lambda x: x.rate)
            break
    else:
        best_record = max(records, key=lambda x: x.rate)

    return best_record


def get_country_name_by_code(code):
    countries_map = {
        'AD': 'Андорра',
        'AE': 'ОАЭ',
        'AF': 'Афганистан',
        'AG': 'Антигуа и Барбуда',
        'AI': 'Ангилья',
        'AL': 'Албания',
        'AM': 'Армения',
        'AO': 'Ангола',
        'AQ': 'Антарктида',
        'AR': 'Аргентина',
        'AS': 'Американское Самоа',
        'AT': 'Австрия',
        'AU': 'Австралия',
        'AW': 'Аруба',
        'AX': 'Аландские острова',
        'AZ': 'Азербайджан',
        'BA': 'Босния и Герцеговина',
        'BB': 'Барбадос',
        'BD': 'Бангладеш',
        'BE': 'Бельгия',
        'BF': 'Буркина-Фасо',
        'BG': 'Болгария',
        'BH': 'Бахрейн',
        'BI': 'Бурунди',
        'BJ': 'Бенин',
        'BL': 'Сен-Бартелеми',
        'BM': 'Бермуды',
        'BN': 'Бруней',
        'BO': 'Боливия',
        'BQ': 'Бонэйр, Синт-Эстатиус и Саба',
        'BR': 'Бразилия',
        'BS': 'Багамы',
        'BT': 'Бутан',
        'BV': 'Остров Буве',
        'BW': 'Ботсвана',
        'BY': 'Белоруссия',
        'BZ': 'Белиз',
        'CA': 'Канада',
        'CC': 'Кокосовые острова',
        'CD': 'Демократическая Республика Конго',
        'CF': 'ЦАР',
        'CG': 'Республика Конго',
        'CH': 'Швейцария',
        'CI': 'Кот-д’Ивуар',
        'CK': 'Острова Кука',
        'CL': 'Чили',
        'CM': 'Камерун',
        'CN': 'КНР',
        'CO': 'Колумбия',
        'CR': 'Коста-Рика',
        'CU': 'Куба',
        'CV': 'Кабо-Верде',
        'CW': 'Кюрасао',
        'CX': 'Остров Рождества',
        'CY': 'Кипр',
        'CZ': 'Чехия',
        'DE': 'Германия',
        'DJ': 'Джибути',
        'DK': 'Дания',
        'DM': 'Доминика',
        'DO': 'Доминиканская Республика',
        'DZ': 'Алжир',
        'EC': 'Эквадор',
        'EE': 'Эстония',
        'EG': 'Египет',
        'EH': 'САДР',
        'ER': 'Эритрея',
        'ES': 'Испания',
        'ET': 'Эфиопия',
        'EU': 'Европейский союз',
        'FI': 'Финляндия',
        'FJ': 'Фиджи',
        'FK': 'Фолклендские острова',
        'FM': 'Микронезия',
        'FO': 'Фареры',
        'FR': 'Франция',
        'GA': 'Габон',
        'GB': 'Великобритания',
        'GD': 'Гренада',
        'GE': 'Грузия',
        'GF': 'Гвиана',
        'GG': 'Гернси',
        'GH': 'Гана',
        'GI': 'Гибралтар',
        'GL': 'Гренландия',
        'GM': 'Гамбия',
        'GN': 'Гвинея',
        'GP': 'Гваделупа',
        'GQ': 'Экваториальная Гвинея',
        'GR': 'Греция',
        'GS': 'Южная Георгия и Южные Сандвичевы Острова',
        'GT': 'Гватемала',
        'GU': 'Гуам',
        'GW': 'Гвинея-Бисау',
        'GY': 'Гайана',
        'HK': 'Гонконг',
        'HM': 'Херд и Макдональд',
        'HN': 'Гондурас',
        'HR': 'Хорватия',
        'HT': 'Гаити',
        'HU': 'Венгрия',
        'ID': 'Индонезия',
        'IE': 'Ирландия',
        'IL': 'Израиль',
        'IM': 'Остров Мэн',
        'IN': 'Индия',
        'IO': 'Британская территория в Индийском океане',
        'IQ': 'Ирак',
        'IR': 'Иран',
        'IS': 'Исландия',
        'IT': 'Италия',
        'JE': 'Джерси',
        'JM': 'Ямайка',
        'JO': 'Иордания',
        'JP': 'Япония',
        'KE': 'Кения',
        'KG': 'Киргизия',
        'KH': 'Камбоджа',
        'KI': 'Кирибати',
        'KM': 'Коморы',
        'KN': 'Сент-Китс и Невис',
        'KP': 'КНДР',
        'KR': 'Республика Корея',
        'KW': 'Кувейт',
        'KY': 'Острова Кайман',
        'KZ': 'Казахстан',
        'LA': 'Лаос',
        'LB': 'Ливан',
        'LC': 'Сент-Люсия',
        'LI': 'Лихтенштейн',
        'LK': 'Шри-Ланка',
        'LR': 'Либерия',
        'LS': 'Лесото',
        'LT': 'Литва',
        'LU': 'Люксембург',
        'LV': 'Латвия',
        'LY': 'Ливия',
        'MA': 'Марокко',
        'MC': 'Монако',
        'MD': 'Молдавия',
        'ME': 'Черногория',
        'MF': 'Сен-Мартен',
        'MG': 'Мадагаскар',
        'MH': 'Маршалловы Острова',
        'MK': 'Македония',
        'ML': 'Мали',
        'MM': 'Мьянма',
        'MN': 'Монголия',
        'MO': 'Макао',
        'MP': 'Северные Марианские Острова',
        'MQ': 'Мартиника',
        'MR': 'Мавритания',
        'MS': 'Монтсеррат',
        'MT': 'Мальта',
        'MU': 'Маврикий',
        'MV': 'Мальдивы',
        'MW': 'Малави',
        'MX': 'Мексика',
        'MY': 'Малайзия',
        'MZ': 'Мозамбик',
        'NA': 'Намибия',
        'NC': 'Новая Каледония',
        'NE': 'Нигер',
        'NF': 'Остров Норфолк',
        'NG': 'Нигерия',
        'NI': 'Никарагуа',
        'NL': 'Нидерланды',
        'NO': 'Норвегия',
        'NP': 'Непал',
        'NR': 'Науру',
        'NU': 'Ниуэ',
        'NZ': 'Новая Зеландия',
        'OM': 'Оман',
        'PA': 'Панама',
        'PE': 'Перу',
        'PF': 'Французская Полинезия',
        'PG': 'Папуа — Новая Гвинея',
        'PH': 'Филиппины',
        'PK': 'Пакистан',
        'PL': 'Польша',
        'PM': 'Сен-Пьер и Микелон',
        'PN': 'Острова Питкэрн',
        'PR': 'Пуэрто-Рико',
        'PS': 'Государство Палестина',
        'PT': 'Португалия',
        'PW': 'Палау',
        'PY': 'Парагвай',
        'QA': 'Катар',
        'RE': 'Реюньон',
        'RO': 'Румыния',
        'RS': 'Сербия',
        'RU': 'Россия',
        'RW': 'Руанда',
        'SA': 'Саудовская Аравия',
        'SB': 'Соломоновы Острова',
        'SC': 'Сейшельские Острова',
        'SD': 'Судан',
        'SE': 'Швеция',
        'SG': 'Сингапур',
        'SH': 'Острова Святой Елены, Вознесения и Тристан-да-Кунья',
        'SI': 'Словения',
        'SJ': 'Шпицберген и Ян-Майен',
        'SK': 'Словакия',
        'SL': 'Сьерра-Леоне',
        'SM': 'Сан-Марино',
        'SN': 'Сенегал',
        'SO': 'Сомали',
        'SR': 'Суринам',
        'SS': 'Южный Судан',
        'ST': 'Сан-Томе и Принсипи',
        'SV': 'Сальвадор',
        'SX': 'Синт-Мартен',
        'SY': 'Сирия',
        'SZ': 'Свазиленд',
        'TC': 'Тёркс и Кайкос',
        'TD': 'Чад',
        'TF': 'Французские Южные и Антарктические Территории',
        'TG': 'Того',
        'TH': 'Таиланд',
        'TJ': 'Таджикистан',
        'TK': 'Токелау',
        'TL': 'Восточный Тимор',
        'TM': 'Туркмения',
        'TN': 'Тунис',
        'TO': 'Тонга',
        'TR': 'Турция',
        'TT': 'Тринидад и Тобаго',
        'TV': 'Тувалу',
        'TW': 'Китайская Республика',
        'TZ': 'Танзания',
        'UA': 'Украина',
        'UG': 'Уганда',
        'UM': 'Внешние малые острова (США)',
        'US': 'США',
        'UY': 'Уругвай',
        'UZ': 'Узбекистан',
        'VA': 'Ватикан',
        'VC': 'Сент-Винсент и Гренадины',
        'VE': 'Венесуэла',
        'VG': 'Виргинские Острова (Великобритания)',
        'VI': 'Виргинские Острова (США)',
        'VN': 'Вьетнам',
        'VU': 'Вануату',
        'WF': 'Уоллис и Футуна',
        'WS': 'Самоа',
        'YE': 'Йемен',
        'YT': 'Майотта',
        'ZA': 'ЮАР',
        'ZM': 'Замбия',
        'ZW': 'Зимбабве'
    }

    return countries_map.get(code, '')