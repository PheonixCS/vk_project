#
import os
import logging

from PIL import ImageFont, Image, ImageDraw
from django.conf import settings
from textwrap import wrap
from constance import config

from posting.core.images import is_text_fit_to_width, calculate_max_len_in_chars

log = logging.getLogger('posting.horoscopes')


def transfer_horoscope_to_image(raw_text, font_name='museo_cyrl.otf'):
    log.debug('transfer_horoscope_to_image started')
    file_name = 'horoscopes{}.jpg'.format(hash(raw_text) % 1000)

    font_title = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'posting/extras/fonts', font_name),
                                    config.HOROSCOPES_FONT_TITLE)
    body_font_size = config.HOROSCOPES_FONT_BODY
    font_body = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'posting/extras/fonts', font_name),
                                   body_font_size)

    raw_title_text = raw_text.split('\n')[0]
    title_text = raw_title_text.upper()
    body_text_raw = raw_text.split('\n')[1:]
    body_text = '\n'.join(body_text_raw)
    body_text.capitalize()

    img = Image.open(os.path.join(settings.BASE_DIR, 'posting/extras/image_templates', 'horoscopes_template.jpg'))

    paste_text_to_center(img, font_title, title_text, 'title')

    # TODO really bad implementation
    while not paste_text_to_center(img, font_body, body_text, 'body', text_align='justify'):
        body_font_size -= 5
        font_body = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'posting/extras/fonts', font_name),
                                       body_font_size)

    if file_name.endswith('.jpg'):
        img.save(file_name, 'JPEG', quality=95, progressive=True)
    else:
        img.save(file_name)

    log.debug('transfer_horoscope_to_image finished, file {}'.format(file_name))
    return file_name


def paste_text_to_center(img_obj, font_obj, text, text_type, text_align='center'):
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
        max_text = max(wrapped_text, key=lambda line: font_obj.getsize(line)[0])
        text_width = font_obj.getsize(max_text)[0]
        text_height = font_obj.getsize(wrapped_text[0])[1] * len(wrapped_text) + 10 * (len(wrapped_text) - 1)

        if text_height >= custom_height:
            return 0

        text = '\n'.join(wrapped_text)

    draw = ImageDraw.Draw(img_obj)

    x = (img_obj.width - text_width - width_offset) // 2 + width_offset_left
    y = (custom_height - text_height) // 2 + height_offset_top

    if text_align == 'justify':
        text_lines = text.split('\n')

        space_width = font_obj.getsize(' ')[0]
        maximum_text = max(text_lines, key=lambda line: font_obj.getsize(line)[0])
        maximum_text_width = font_obj.getsize(maximum_text)[0]

        for number, line in enumerate(text_lines):
            text_width = font_obj.getsize(line)[0]
            if text_width == maximum_text_width:
                continue

            words_without_spaces = line.split(' ')
            just_words_width = font_obj.getsize(''.join(words_without_spaces))[0]

            minimum_extra_width = maximum_text_width - just_words_width
            extra_space_count = round(minimum_extra_width / space_width)
            spaces_per_join = extra_space_count // len(words_without_spaces)

            if extra_space_count < len(words_without_spaces):
                result = ' '.join(words_without_spaces)
            elif extra_space_count % len(words_without_spaces) == 0:
                result = (' ' * spaces_per_join).join(words_without_spaces)
            else:
                over_extra_spaces = extra_space_count - spaces_per_join * len(words_without_spaces)

                first_group = words_without_spaces[:over_extra_spaces]
                second_group = words_without_spaces[over_extra_spaces:]
                if len(first_group) == 1:
                    temp = first_group[0] + ' ' * (spaces_per_join + over_extra_spaces)
                else:
                    temp = (' ' * (spaces_per_join + over_extra_spaces)).join(first_group)
                temp_list = [temp, ]
                temp_list.extend(second_group)
                result = (' ' * spaces_per_join).join(temp_list)

            result_width = font_obj.getsize(result)[0]

            text_lines[number] = result
        text = '\n'.join(text_lines)

        draw.multiline_text((x, y), text, white_color, font=font_obj, align='left', spacing=10)
    else:
        draw.multiline_text((x, y), text, white_color, font=font_obj, align=text_align, spacing=10)

    return 1
