import logging
import re
from difflib import SequenceMatcher

from phonenumbers import PhoneNumberMatcher
from urlextract import URLExtract

from scraping.models import Record
from settings.models import Setting

log = logging.getLogger('scraping.filters')

MIN_STRING_MATCH_RATIO = Setting.get_value(key='MIN_STRING_MATCH_RATIO')


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
               SequenceMatcher(None, record['text'], record_in_db.text).ratio() < MIN_STRING_MATCH_RATIO):
            filtered_records.append(record)
        else:
            log.debug('record {} was filtered'.format(record['id']))

    # TODO проверка изображений на дубликаты
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
                    log.debug('filter record due to unsuitable attachments'.format(record.get('id', None)))
                    break
                if attachment['type'] == 'doc' and attachment['doc']['ext'] != 'gif':
                    log.debug('filter record due to unsuitable attachments'.format(record.get('id', None)))
                    break
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
                          attachment['type'] == 'doc' and attachment['doc']['ext'] == 'gif'])
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
