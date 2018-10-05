#
import os

from PIL import ImageFont, Image, ImageDraw
from django.conf import settings
from textwrap import wrap

from posting.poster import (
    calculate_max_len_in_chars,
    is_text_fit_to_width
)


def transfer_horoscope_to_image(raw_text, font_name='bebas_neue_ru.ttf'):
    file_name = 'test.jpg'

    font_60 = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'posting/extras/fonts', font_name), 60)
    font_40 = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'posting/extras/fonts', font_name), 40)

    title_text = raw_text.split('\n')[0]
    body_text = ''.join(raw_text.split('\n')[1:])

    img = Image.open(os.path.join(settings.BASE_DIR, 'posting/extras/image_templates', 'horoscopes_template.jpg'))

    paste_text_to_center(img, font_60, title_text, 75)
    paste_text_to_center(img, font_40, body_text, 200)

    if file_name.endswith('.jpg'):
        img.save(file_name, 'JPEG', quality=95, progressive=True)
    else:
        img.save(file_name)

    return file_name


def paste_text_to_center(img_obj, font_obj, text, height):
    black_color = (0, 0, 0)

    image_width, image_height = img_obj.width, img_obj.height

    if not is_text_fit_to_width(text, len(text), image_width - 10, font_obj):
        text_max_width_in_chars = calculate_max_len_in_chars(text, image_width, font_obj)
        text = '\n'.join(wrap(text, text_max_width_in_chars))

    draw = ImageDraw.Draw(img_obj)

    draw.multiline_text((0, height), text, black_color, font=font_obj, align='center')

