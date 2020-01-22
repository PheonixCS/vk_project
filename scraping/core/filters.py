import logging
import re
from difflib import SequenceMatcher

from constance import config
from phonenumbers import PhoneNumberMatcher
from urlextract import URLExtract

from scraping.models import Record

log = logging.getLogger('scraping.core.filters')


# Standard filters
def filter_out_copies(records):
    log.info('filter_out_copies called')
    records_in_db = Record.objects.all()

    if not records_in_db:
        log.info('no records in db')
        return records

    filtered_records = []

    for record in records:
        if any(record_in_db for record_in_db in records_in_db if
               SequenceMatcher(None, record['text'], record_in_db.text).ratio() < config.MIN_STRING_MATCH_RATIO):
            filtered_records.append(record)
        else:
            log.debug('record {} was filtered'.format(record['id']))

    return filtered_records


def filter_out_records_with_unsuitable_attachments(records):
    suitable_attachments = ['video', 'audio', 'doc', 'photo']

    filtered_records = []
    for record in records:
        attachments = record.get('attachments')
        if not attachments:
            filtered_records.append(record)
        else:
            for attachment in attachments:
                if attachment['type'] not in suitable_attachments:
                    log.debug('filter record {} due to unsuitable attachments'.format(record.get('id', None)))
                    break
                if attachment['type'] == 'doc' and attachment['doc']['ext'] != 'gif':
                    log.debug('filter record {} due to unsuitable attachments'.format(record.get('id', None)))
                    break
            else:
                filtered_records.append(record)

    return filtered_records


def filter_out_records_with_small_images(records, min_quantity_of_pixels=config.MIN_QUANTITY_OF_PIXELS):
    filtered_records = []
    for record in records:
        attachments = record.get('attachments')
        if not attachments:
            filtered_records.append(record)
            continue

        for attachment in attachments:
            if attachment['type'] != 'photo':
                continue

            width = attachment['photo'].get('width', None)
            height = attachment['photo'].get('height', None)
            if not width or not height:
                log.debug(f'record {record.get("id", None)} photo has no dimensions')
                continue

            if width < min_quantity_of_pixels or height < min_quantity_of_pixels:
                log.debug(f'filter record {record.get("id", None)} due to min width or height value')
                break
        else:
            filtered_records.append(record)

    return filtered_records


def marked_as_ads_filter(item):
    if item.get('marked_as_ads', 0):
        log.debug('delete {} as ad: marked_as_ads_filter'.format(item['id']))
        return False
    return True


def copy_history_filter(item):
    if 'copy_history' in item:
        log.debug('delete {} as ad: copy_history_filter'.format(item['id']))
        return False
    return True


def phone_numbers_filter(item):
    if PhoneNumberMatcher(text=item['text'], region='RU').has_next():
        log.debug('delete {} as ad: phone_numbers_filter'.format(item['id']))
        return False
    return True


def urls_filter(item):
    extractor = URLExtract()
    if extractor.has_urls(item['text']):
        log.debug('delete {} as ad: urls_filter'.format(item['id']))
        return False
    return True


def email_filter(item):
    if re.findall(r'[\w.-]+ @ [\w.-]+', item['text']):
        log.debug('delete {} as ad: email_filter'.format(item['id']))
        return False
    return True


def article_filter(item):
    if item.get('attachments'):
        for attachment in item['attachments']:
            if attachment['type'] == 'link':
                log.debug('delete {} as ad: article_filter'.format(item['id']))
                return False
    return True


def vk_link_filter(item):
    if re.findall(r'\[.*?\|.*?\]', item['text']):
        log.debug('delete {} as ad: vk_link_filter'.format(item['id']))
        return False
    return True


def vk_link_filter_2(item):
    if re.findall(r'.*vk.com/.*', item['text']):
        log.debug('delete {} as ad: vk_link_filter2'.format(item['id']))
        return False
    return True


def raffle_filter(item):
    if 'конкурс' in item['text'].lower() or 'розыгрыш' in item['text'].lower():
        log.debug('delete {} as ad: raffle filter'.format(item['id']))
        return False
    return True


def filter_out_ads(records):
    log.info('filter_out_ads called')
    filters = (
        marked_as_ads_filter,
        copy_history_filter,
        phone_numbers_filter,
        urls_filter,
        email_filter,
        article_filter,
        vk_link_filter,
        raffle_filter,
        vk_link_filter_2
    )
    filtered_records = [record for record in records if all(filter(record) for filter in filters)]
    return filtered_records


# Custom filters
def min_quantity_of_line_breaks_filter(item, custom_filter):
    if len(item.get('text', str()).splitlines()) < custom_filter.min_quantity_of_line_breaks:
        log.debug('delete {} because of custom filter: min_quantity_of_line_breaks'.format(item['id']))
        return False
    return True


def min_text_length_filter(item, custom_filter):
    if len(item.get('text', str())) < custom_filter.min_text_length:
        log.debug('delete {} because of custom filter: min_text_length'.format(item['id']))
        return False
    return True


def min_quantity_of_videos_filter(item, custom_filter):
    number_of_videos = len(
        [attachment for attachment in item.get('attachments', []) if attachment['type'] == 'video'])
    if number_of_videos < custom_filter.min_quantity_of_videos:
        log.debug('delete {} because of custom filter: min_quantity_of_videos'.format(item['id']))
        return False
    return True


def min_quantity_of_films_filter(item, custom_filter):
    film_min_duration_in_seconds = 1200
    number_of_films = len([att for att in item.get('attachments', []) if
                           att['type'] == 'video' and att['video']['duration'] >= film_min_duration_in_seconds])
    if number_of_films < custom_filter.min_quantity_of_films:
        log.debug('delete {} because of custom filter: min_quantity_of_films'.format(item['id']))
        return False
    return True


def min_quantity_of_images_filter(item, custom_filter):
    number_of_images = len(
        [attachment for attachment in item.get('attachments', []) if attachment['type'] == 'photo'])
    if number_of_images < custom_filter.min_quantity_of_images:
        log.debug('delete {} because of custom filter: min_quantity_of_images'.format(item['id']))
        return False
    return True


def min_quantity_of_gifs_filter(item, custom_filter):
    number_of_gifs = len([attachment for attachment in item.get('attachments', []) if
                          attachment['type'] == 'doc' and attachment['doc']['ext'] == 'gif'
                          and attachment['doc']['owner_id'] > 0])
    if number_of_gifs < custom_filter.min_quantity_of_gifs:
        log.debug('delete {} because of custom filter: min_quantity_of_gifs'.format(item['id']))
        return False
    return True


def min_quantity_of_audios_filter(item, custom_filter):
    number_of_audios = len(
        [attachment for attachment in item.get('attachments', []) if attachment['type'] == 'audio'])
    if number_of_audios < custom_filter.min_quantity_of_audios:
        log.debug('delete {} because of custom filter: min_quantity_of_audios'.format(item['id']))
        return False
    return True


def filter_with_custom_filters(records, custom_filters):
    filtered_records = []
    for custom_filter in custom_filters:
        filters = tuple()
        if custom_filter.min_quantity_of_line_breaks:
            filters += (min_quantity_of_line_breaks_filter,)

        if custom_filter.min_text_length:
            filters += (min_text_length_filter,)

        if custom_filter.min_quantity_of_videos:
            filters += (min_quantity_of_videos_filter,)

        if custom_filter.min_quantity_of_films:
            filters += (min_quantity_of_films_filter,)

        if custom_filter.min_quantity_of_images:
            filters += (min_quantity_of_images_filter,)

        if custom_filter.min_quantity_of_gifs:
            filters += (min_quantity_of_gifs_filter,)

        if custom_filter.min_quantity_of_audios:
            filters += (min_quantity_of_audios_filter,)

        filtered_records.extend([record for record in records if all(
            filter(record, custom_filter) for filter in filters) and record not in filtered_records])

    return filtered_records
