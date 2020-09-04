import logging
import os
from random import randint
from textwrap import wrap
from time import time

from PIL import ImageFont, Image, ImageDraw
from constance import config
from django.conf import settings

from posting.core.images import is_text_fit_to_width, calculate_max_len_in_chars

log = logging.getLogger('posting.horoscopes')


def transfer_horoscope_to_image(raw_text, font_name='museo_cyrl.otf'):
    log.debug('transfer_horoscope_to_image started')
    file_name = f'horoscopes{randint(1, int(time())):0<10}.jpg'

    horoscopes_font_title = config.HOROSCOPES_FONT_TITLE
    font_path = os.path.join(settings.BASE_DIR, 'posting/extras/fonts', 'bebas_neue_ru.ttf')
    font_title = ImageFont.truetype(font_path, horoscopes_font_title)

    body_font_size = config.HOROSCOPES_FONT_BODY
    font_path = os.path.join(settings.BASE_DIR, 'posting/extras/fonts', font_name)
    font_body = ImageFont.truetype(font_path, body_font_size)

    raw_title_text = raw_text.split('\n')[0]
    title_text = raw_title_text.upper()

    body_text_raw = raw_text.split('\n')[1:]
    body_text = '\n'.join(body_text_raw)
    body_text.capitalize()

    img = Image.open(os.path.join(settings.BASE_DIR, 'posting/extras/image_templates', 'horoscope_template_new.jpg'))

    paste_text_to_center(img, font_title, title_text, 'title')

    # TODO really bad implementation
    while not paste_text_to_center(img, font_body, body_text, 'body', text_align='center'):
        body_font_size -= 5
        font_body = ImageFont.truetype(font_path, body_font_size)

    if file_name.endswith('.jpg'):
        img.save(file_name, 'JPEG', quality=95, progressive=True)
    else:
        img.save(file_name)

    log.debug(f'transfer_horoscope_to_image finished, file {file_name}')
    return file_name


def paste_text_to_center(img_obj, font_obj, text, text_type, text_align='center', spacing=10):
    white_color = (255, 255, 255)

    text_width = font_obj.getsize(text)[0]
    text_height = font_obj.getsize(text)[1]

    if text_type == 'title':
        width_offset_left = 0
        height_offset_top = 0
        custom_height = 130
    else:
        width_offset_left = 70
        height_offset_top = 180
        custom_height = 1080 - height_offset_top

    width_offset = width_offset_left * 2

    image_width, image_height = img_obj.width, img_obj.height

    if not is_text_fit_to_width(text, len(text), image_width - width_offset, font_obj):
        text_max_width_in_chars = calculate_max_len_in_chars(text, image_width - width_offset, font_obj)
        wrapped_text = wrap(text, text_max_width_in_chars)
        max_text = max(wrapped_text, key=lambda line: font_obj.getsize(line)[0])
        text_width = font_obj.getsize(max_text)[0]
        text_height = font_obj.getsize(wrapped_text[0])[1] * len(wrapped_text) + 10 * (len(wrapped_text) - 1)

        if text_height >= custom_height:
            return 0

        text = '\n'.join(wrapped_text)

    draw = ImageDraw.Draw(img_obj)

    x = (img_obj.width - text_width - width_offset) // 2 + width_offset_left

    if text_type == 'title':
        y = (custom_height - text_height) // 2 + height_offset_top
    else:
        y = height_offset_top  # all horoscopes will be at the same height

    draw.multiline_text((x, y), text, white_color, font=font_obj, align=text_align, spacing=spacing)

    return 1
