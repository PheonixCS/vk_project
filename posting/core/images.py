import logging
import os
import time
from math import ceil
from textwrap import wrap

import pytesseract
from PIL import Image, ImageFont, ImageDraw, ImageFile
from constance import config
from django.conf import settings

from posting.extras.transforms import RGBTransform

log = logging.getLogger('posting.core.images')


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


def fill_image_with_text(filepath, text, font_name=None):
    log.debug('fill_image_with_text called')
    font_name = font_name or config.FONT_NAME
    if not text:
        log.debug('got no text in fill_image_with_text')
        return

    black_color = (0, 0, 0)

    with Image.open(os.path.join(settings.BASE_DIR, filepath)) as temp:
        image_width, image_height = temp.width, temp.height

    # size in pixels
    size = calculate_text_size_on_image(box=(image_width, image_height))

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
    draw.multiline_text((x, y), text, black_color, font=font, align='center')

    if filepath.endswith('.jpg'):
        image.save(filepath, 'JPEG', quality=95, progressive=True)
    else:
        image.save(filepath)
    log.debug('fill_image_with_text finished')


def divergence(one, two):
    return abs(one - two) / max(one, two)


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
    min_size = min(sizes, key=lambda size: size[0] * size[1])
    return min_size


def calculate_size_from_one_side(origin_width, origin_height, width=None, height=None):
    r_width, r_height = origin_width, origin_height

    if width:
        r_width, r_height = int(width), int(width / origin_width * origin_height)

    if height:
        r_width, r_height = int(origin_width / origin_height * height), int(height)

    log.debug('calculate_size_from_one_side finished with sizes orig - {}:{}, new - {}:{}'.format(
        origin_width, origin_height, r_width, r_height
    ))

    return r_width, r_height


def resize_image_aspect_ratio_by_two_sides(image_object, width, height):
    # maybe solution of problem
    # https://stackoverflow.com/questions/12984426/python-pil-ioerror-image-file-truncated-with-big-images
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    log.debug('resize_image_aspect_ratio_by_two_sides called with {}:{}'.format(width, height))

    orig_width = image_object.size[0]
    orig_height = image_object.size[1]

    if orig_width / orig_height >= width / height:
        new_size = calculate_size_from_one_side(orig_width, orig_height, height=height)
    else:
        new_size = calculate_size_from_one_side(orig_width, orig_height, width=width)
    log.debug('resize_image_aspect_ratio_by_two_sides finished')

    try:
        resized_image = image_object.resize(new_size, resample=Image.NEAREST)
    except:
        log.error('error in resize_image_aspect_ratio_by_one_side', exc_info=True)
        return

    return resized_image


def resize_image_aspect_ratio_by_one_side(image_object, width=None, height=None):
    # maybe solution of problem
    # https://stackoverflow.com/questions/12984426/python-pil-ioerror-image-file-truncated-with-big-images
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    log.debug('resize_image_aspect_ratio_by_one_side called with {}:{}'.format(width, height))

    new_size = calculate_size_from_one_side(image_object.size[0], image_object.size[1], width, height)

    try:
        resized_image = image_object.resize(new_size, resample=Image.NEAREST)
    except:
        log.error('error in resize_image_aspect_ratio_by_one_side', exc_info=True)
        return

    return resized_image


def merge_poster_and_three_images(poster, images):
    log.debug('merge_poster_and_three_images called')

    offset = 3 * config.SIX_IMAGES_OFFSET
    filepath = f'temp_{poster}'

    if len(images) != 3:
        log.warning('number of images in merge_poster_and_three_images not equal 3!')
    elif len(images) < 3:
        log.error('lack of images in merge_poster_and_three_images!')
        # TODO catch this state

    images_sizes = [Image.open(os.path.join(settings.BASE_DIR, image)).size for image in images]
    poster_width, poster_height = Image.open(os.path.join(settings.BASE_DIR, poster)).size

    poster_image_object = Image.open(os.path.join(settings.BASE_DIR, poster))

    required_width = min([size[0] for size in images_sizes])
    required_height = min([size[1] for size in images_sizes])
    height = required_height * 3 + offset * 2

    poster_width, poster_height = calculate_size_from_one_side(poster_width, poster_height, height=height)
    poster_height = int(poster_height)
    poster_width = int(poster_width)
    width = poster_width + offset + required_width

    result = Image.new('RGB', (width, height), 'White')

    poster_image_object = resize_image_aspect_ratio_by_two_sides(poster_image_object, width=poster_width, height=height)
    try:
        result.paste(poster_image_object)
    except ValueError:
        cropped = poster_image_object.crop((0, 0, poster_width, poster_height))
        result.paste(cropped)

    log.debug('for starts in merge_poster_and_three_images')
    for index, image in enumerate(images):
        x = poster_width + offset
        y = index * (required_height + offset)

        img_object = Image.open(os.path.join(settings.BASE_DIR, image))
        img_object = resize_image_aspect_ratio_by_two_sides(img_object, width=required_width, height=required_height)
        log.debug('cropping in loop')
        cropped = img_object.crop((0, 0, required_width, required_height))
        result.paste(cropped, (x, y, x + required_width, y + required_height))
        log.debug('for loop body end')
    log.debug('for end and resize result')
    result = resize_image_aspect_ratio_by_one_side(result, width=1920)
    log.debug('saving')
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

    result = Image.new('RGB', (min_width * 3 + offset * 2, min_height * 2 + offset), 'White')

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


def paste_abstraction_on_template(template, abstraction):
    log.debug('paste_abstraction_on_template called')

    template = Image.open(template).convert('RGBA')
    abstraction = Image.open(abstraction).convert('RGBA')

    if abstraction.size[1] > abstraction.size[0]:
        abstraction = resize_image_aspect_ratio_by_one_side(abstraction, width=template.size[0])
    else:
        abstraction = resize_image_aspect_ratio_by_one_side(abstraction, height=template.size[0])

    abstraction = crop_center(abstraction, template.size)

    resulting_image = Image.alpha_composite(abstraction, template)
    resulting_image = resulting_image.convert('RGB')

    resulting_name = f'result_{hash(time.process_time())}.jpg'
    resulting_image.save(resulting_name, 'JPEG', quality=95, progressive=True)

    log.debug('paste_abstraction_on_template finished')
    return resulting_name


def paste_text_on_image(image_name, text, position='top', color='black', size=None, pos_offset=0):
    image = Image.open(os.path.join(settings.BASE_DIR, image_name))
    image_width, image_height = image.width, image.height

    if not size:
        size = calculate_text_size_on_image(box=(image_width, image_height))

    font = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'posting/extras/fonts', config.FONT_NAME), size)

    # Normalize text
    normalized_text = []
    for paragraph in text.split('\n'):
        if not paragraph:
            continue
        if not is_text_fit_to_width(paragraph, len(paragraph), image_width - config.IMAGE_SIDE_OFFSET_ABS, font):
            text_max_width_in_chars = calculate_max_len_in_chars(paragraph,
                                                                 image_width - config.IMAGE_SIDE_OFFSET_ABS,
                                                                 font)
            paragraph = '\n'.join(wrap(paragraph, text_max_width_in_chars))
        normalized_text.append(paragraph)

    text = '\n'.join(normalized_text)
    text_width, text_height = font.getsize_multiline(text, spacing=config.IMAGE_SPACING_ABS)

    if text:
        expand_image_with_white_color(image_name, text_height + config.IMAGE_SIDE_OFFSET_ABS * 3)
    image = Image.open(os.path.join(settings.BASE_DIR, image_name))
    draw = ImageDraw.Draw(image)
    image_width, image_height = image.width, image.height

    position = calculate_text_position_on_image(
        image_box=(image_width, image_height),
        text_box=(text_width, text_height),
        anchor=position,
        offset=pos_offset)

    draw.multiline_text(position, text,
                        font=font,
                        spacing=config.IMAGE_SPACING_ABS,
                        align='center',
                        fill=color,
                        )

    new_name = image_name

    if new_name.endswith('.jpg'):
        image.save(new_name, 'JPEG', quality=95, progressive=True)
    else:
        image.save(new_name)

    return position


def calculate_text_size_on_image(box, percent=None):
    percent = percent or config.FONT_SIZE_PERCENT
    image_width, image_height = box

    if percent < 1:
        percent = 1

    # size in pixels
    size = ceil(image_height * percent / 100)

    return size


def calculate_text_position_on_image(image_box, text_box, anchor, offset=0):
    anchors = ('top', 'bottom')
    if anchor not in anchors:
        raise ValueError('Anchor parameter invalid. Must be in {}'.format(anchors))

    side_offest = config.IMAGE_SIDE_OFFSET_ABS

    image_width, image_height = image_box
    text_width, text_height = text_box

    if anchor == 'top':
        x = (image_width - text_width) // 2
        y = side_offest + offset
        return x, y

    elif anchor == 'bottom':
        x = (image_width - text_width) // 2
        y = image_height - text_height - side_offest - offset
        return x, y


def crop_center(image, size):
    """

    :type image: PIL.Image.Image
    :type size: tuple
    :rtype: PIL.Image.Image
    """

    orig_size = image.width, image.height

    if size[0] > orig_size[0] or size[1] > orig_size[1]:
        raise ValueError('Input size cannot be bigger than original image size!')

    centered_box = calculate_centered_box(size, orig_size)

    result = image.crop(centered_box)

    return result


def calculate_centered_box(required_size, orig_size):
    delta_x = (orig_size[0] - required_size[0]) // 2
    delta_y = (orig_size[1] - required_size[1]) // 2

    left = delta_x
    upper = delta_y
    right = delta_x + required_size[0]
    bottom = delta_y + required_size[1]

    box = left, upper, right, bottom

    return box


def paste_text_on_music_image(image_name, music_text):
    image = Image.open(os.path.join(settings.BASE_DIR, image_name))
    image_width, image_height = image.width, image.height

    primary_size = calculate_text_size_on_image(box=(image_width, image_height))
    secondary_size = calculate_text_size_on_image(box=(image_width, image_height), percent=config.FONT_SIZE_PERCENT - 2)

    primary_color = 'black'
    secondary_color = 'grey'

    music_text_list = music_text.split('\n')
    if len(music_text_list) > 1:
        secondary_text = '\n'.join(music_text_list[1:])
        paste_text_on_image(image_name, secondary_text, size=secondary_size, color=secondary_color)

    primary_text = music_text_list[0]
    paste_text_on_image(image_name, primary_text, size=primary_size, color=primary_color)


def sort_images_for_movies(files):
    images = [
        {'size': Image.open(os.path.join(settings.BASE_DIR, image)).size, 'file': image} for image in files
    ]

    width = [size[0] for size in images_sizes]
    height = [size[1] for size in images_sizes]

    return all(height >= width for width, height in zip(width, height))
