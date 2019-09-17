import ast
import logging
import os
from collections import Counter
from datetime import timedelta
from random import shuffle
from typing import List

import requests
from constance import config
from django.conf import settings
from django.db.models import Count
from django.db.models.query import QuerySet
from django.utils import timezone

from posting.core.images import crop_percentage_from_image_edges, color_image_in_tone, paste_text_on_image, \
    mirror_image
from posting.core.mapping import countries, genres
from posting.core.text_utilities import delete_emoji_from_text
from posting.models import Group
from scraping.models import Attachment

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
        paste_text_on_image(image_local_filepath, kwargs.get('text_to_fill'))


def prepare_audio_attachments(audios, is_shuffle=False, is_cut=False):
    if is_shuffle:
        shuffle(audios)

    if is_cut and len(audios) > 1:
        audios = audios[:-1]

    return [f'audio{audio.owner_id}_{audio.audio_id}' for audio in audios]


def find_the_best_post(records: QuerySet, best_ratio, percent=20):
    log.debug('find_the_best_post called')

    eps = 0.1
    records = records.order_by('-rate')

    end_index = int(len(records) / 100 * percent) or 1
    records = records[:end_index]

    for i in range(1, 6):
        exact_ratio_records = [record for record in records if
                               0 <= abs(record.males_females_ratio - best_ratio) <= i * eps]

        if exact_ratio_records:
            best_record = max(exact_ratio_records, key=lambda x: x.rate)
            break
    else:
        best_record = max(records, key=lambda x: x.rate)

    return best_record


def get_country_name_by_code(code):
    return countries.get(code, '')


def get_movies_rating_intervals():
    try:
        intervals_borders = ast.literal_eval(config.TMDB_MOVIE_INTERVALS)
    except SyntaxError:
        intervals_borders = ast.literal_eval(settings.CONFIG['TMDB_MOVIE_INTERVALS'][0])
        log.warning('get_movies_rating_intervals got wrong format from config, return default', exc_info=True)

    return [[value / 10 for value in range(interval[0], interval[1])] for interval in intervals_borders]


def get_next_interval_by_movie_rating(rating):
    rating_intervals = get_movies_rating_intervals()

    for interval in rating_intervals:
        if rating in interval:
            return rating_intervals[(rating_intervals.index(interval) + 1) % len(rating_intervals)]


def get_music_compilation_artist(audios):
    artists = [delete_emoji_from_text(audio.artist) for audio in audios]
    artist, count = Counter(artists).most_common(1)[0]
    if float(count) >= float(len(audios) / 2):
        return artist
    else:
        return None


def get_music_compilation_genre(audios):
    genre_ids = [audio.genre for audio in audios]
    if len(genre_ids) > 1:
        genre_id, count = Counter(genre_ids).most_common(1)[0]
        if float(count) >= float(len(audios) / 2):
            return next((genre for genre in genres if genre['id'] == genre_id), None)
    return None


def find_next_element_by_last_used_id(objects, last_used_object_id):
    return next((obj for obj in objects if obj.id > last_used_object_id), objects[0])


def find_suitable_record(records: QuerySet, best_ratio, divergence=20):
    divergence = divergence / 100
    records = records.order_by('-rate')
    max_male_percent = from_ratio_to_percent(best_ratio) + divergence
    min_male_percent = from_ratio_to_percent(best_ratio) - divergence

    for record in records:
        male_percent = from_ratio_to_percent(record.males_females_ratio)
        if min_male_percent < male_percent < max_male_percent:
            best_record = record
            break
    else:
        best_record = records.first()

    return best_record


def from_ratio_to_percent(ratio):
    result = 1 / (1 + ratio)
    return result


def filter_banned_records(records: QuerySet, banned_types: list) -> QuerySet:
    available_choices = [c[0] for c in Attachment.TYPE_CHOICES]
    for t in banned_types:
        if t not in available_choices:
            raise TypeError(f'attachment {t} is not in available {available_choices}')

    attachment_types = []

    if 'video' in banned_types:
        attachment_types.append('videos')
    if 'picture' in banned_types:
        attachment_types.append('images')
    if 'gif' in banned_types:
        attachment_types.append('gifs')
    if 'audio' in banned_types:
        attachment_types.append('audios')

    for attachment_type in attachment_types:
        annotated = records.annotate(attachments_count=Count(attachment_type))
        records = annotated.exclude(attachments_count__gt=0)

    return records


def get_groups_to_update_sex_statistics(exclude_groups: List[int] = None) -> QuerySet:
    now_time_utc = timezone.now()
    week_ago = now_time_utc - timedelta(days=6, hours=23)

    if not exclude_groups:
        try:
            exclude_groups = ast.literal_eval(config.EXCLUDE_GROUPS_FROM_SEX_STATISTICS_UPDATE)
        except SyntaxError:
            exclude_groups = []
            log.warning('sex_statistics_weekly got wrong format from config', exc_info=True)

    if exclude_groups:
        groups = Group.objects.exclude(group_id__in=exclude_groups)
    else:
        groups = Group.objects.all()

    groups = groups.filter(sex_last_update_date__lte=week_ago)
    log.debug('got {} groups in sex_statistics_weekly'.format(len(groups)))

    return groups
