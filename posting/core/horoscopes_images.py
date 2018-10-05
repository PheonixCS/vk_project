#
import os
import logging

from PIL import ImageFont, Image, ImageDraw
from django.conf import settings
from textwrap import wrap
from constance import config

from posting.poster import (
    calculate_max_len_in_chars,
    is_text_fit_to_width
)

log = logging.getLogger('posting.horoscopes')


def transfer_horoscope_to_image(raw_text, font_name='bebas_neue_ru.ttf'):
    log.debug('transfer_horoscope_to_image started')
    file_name = 'horoscopes{}.jpg'.format(hash(raw_text) % 1000)

    font_title = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'posting/extras/fonts', font_name),
                                    config.HOROSCOPES_FONT_TITLE)
    font_body = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'posting/extras/fonts', font_name),
                                   config.HOROSCOPES_FONT_BODY)

    title_text = raw_text.split('\n')[0]
    body_text = '\n'.join(raw_text.split('\n')[1:])

    img = Image.open(os.path.join(settings.BASE_DIR, 'posting/extras/image_templates', 'horoscopes_template.jpg'))

    paste_text_to_center(img, font_title, title_text, 'title')
    paste_text_to_center(img, font_body, body_text, 'body')

    if file_name.endswith('.jpg'):
        img.save(file_name, 'JPEG', quality=95, progressive=True)
    else:
        img.save(file_name)

    log.debug('transfer_horoscope_to_image finished, file {}'.format(file_name))
    return file_name


def paste_text_to_center(img_obj, font_obj, text, text_type):
    # black_color = (0, 0, 0)
    white_color = (255, 255, 255)

    text_width = font_obj.getsize(text)[0]
    text_height = font_obj.getsize(text)[1]

    if text_type == 'title':
        width_offset_left = 0
        height_offset_top = 0
        custom_height = 150
    else:
        width_offset_left = 70
        height_offset_top = 150
        custom_height = 1080 - 150

    width_offset = width_offset_left * 2

    image_width, image_height = img_obj.width, img_obj.height

    if not is_text_fit_to_width(text, len(text), image_width - width_offset, font_obj):
        text_max_width_in_chars = calculate_max_len_in_chars(text, image_width - width_offset, font_obj)
        wrapped_text = wrap(text, text_max_width_in_chars)

        text_width = font_obj.getsize(max(wrapped_text, key=len))[0]
        text_height = font_obj.getsize(wrapped_text[0])[1] * len(wrapped_text) + 10*(len(wrapped_text)-1)

        text = '\n'.join(wrapped_text)

    draw = ImageDraw.Draw(img_obj)

    x = (img_obj.width - text_width - width_offset) // 2 + width_offset_left
    y = (custom_height - text_height) // 2 + height_offset_top

    draw.multiline_text((x, y), text, white_color, font=font_obj, align='center', spacing=10)
