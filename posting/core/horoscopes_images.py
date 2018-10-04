#
import os

from PIL import ImageFont, Image, ImageDraw
from django.conf import settings


def transfer_horoscope_to_image(raw_text, font_name='bebas_neue_ru.ttf'):

    font_60 = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'posting/extras/fonts', font_name), 60)
    font_40 = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'posting/extras/fonts', font_name), 40)

    title_text = raw_text.split('\n')[0]
    body_text = ''.join(raw_text.split('\n')[1:])

    img = Image.open(os.path.join(settings.BASE_DIR, 'posting/extras/image_templates', 'horoscopes_template.jpg'))
    draw = ImageDraw.Draw(img)

    paste_text_to_center()


def paste_text_to_center(img_obj, font_obj, text, ):
    pass
