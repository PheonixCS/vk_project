import logging
import os
from collections import Counter

import requests

from posting.models import BackgroundAbstraction
from posting.core.mapping import countries, genres
from posting.core.text_utilities import delete_emoji_from_text
from posting.core.images import crop_percentage_from_image_edges, color_image_in_tone, fill_image_with_text, \
    mirror_image

log = logging.getLogger('posting.poster')


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


def find_the_best_post(records, best_ratio, percent=20):
    log.debug('find_the_best_post called')

    eps = 0.1
    records.sort(key=lambda x: x.rate, reverse=True)

    end_index = int(len(records) / 100 * percent) or 1
    records = records[:end_index]

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
    return countries.get(code, '')


def get_movies_rating_intervals():
    intervals_borders = [(65, 70), (70, 75), (75, 80), (80, 101)]

    return [[value / 10 for value in range(interval[0], interval[1])] for interval in intervals_borders]


def get_next_interval_by_movie_rating(rating):
    rating_intervals = get_movies_rating_intervals()

    for interval in rating_intervals:
        if rating in interval:
            return rating_intervals[(rating_intervals.index(interval) + 1) % len(rating_intervals)]


def get_music_compilation_artist(audios):
    artists = [delete_emoji_from_text(audio.artist) for audio in audios]
    artist, _ = Counter(artists).most_common(1)
    return artist


def get_music_genre_by_number(number):
    return {genre['id']: genre['genre'] for genre in genres}.get(number, '')


def get_music_compilation_genre(audios):
    genres = [get_music_genre_by_number(audio.genre) for audio in audios]
    if len(genres) > 1:
        genre, _ = Counter(genres).most_common(1)
        return genre
    else:
        return ''


def find_next_background_abstraction(last_user_abstraction_id):
    background_abstractions = BackgroundAbstraction.objects.all().order_by('id')
    background_abstraction = next(
        (image for image in background_abstractions if image.id > last_user_abstraction_id),
        background_abstractions[0]
    )
    return background_abstraction
