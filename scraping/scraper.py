import datetime
import re
from difflib import SequenceMatcher
import logging

import vk_requests
from vk_requests.exceptions import VkAPIError
from phonenumbers import PhoneNumberMatcher

from posting.models import User
from scraping.models import Donor, Record, Image, Video
from settings.models import Setting

log = logging.getLogger('scraping.scraper')

VK_API_VERSION = Setting.get_value(key='VK_API_VERSION')
MIN_STRING_MATCH_RATIO = Setting.get_value(key='MIN_STRING_MATCH_RATIO')


def distribute_donors_between_accounts(donors, accounts):
    accounts_with_donors = [{
        'token': token,
        'donors': []
    } for token in accounts]

    for donor in donors:
        account_with_min_donors = min(accounts_with_donors, key=lambda x: len(x['donors']))
        for account in accounts_with_donors:
            if account['token'] == account_with_min_donors['token']:
                account['donors'].append(donor)

    return accounts_with_donors


def create_vk_api_using_service_token(token):
    log.debug('create api called')

    try:
        api = vk_requests.create_api(service_token=token, api_version=VK_API_VERSION)
    except VkAPIError as error_msg:
        log.info('token {} got api error: {}'.format(token, error_msg))
        return None

    return api


def get_wall(api, group_id):
    log.debug('get_wall api called for group {}'.format(group_id))

    try:
        log.debug('get_wall called, got group_id {}'.format(group_id))
        if group_id.isdigit():
            log.debug('group id is digit')
            wall = api.wall.get(owner_id='-{}'.format(group_id),
                                filter='owner',
                                api_version=VK_API_VERSION)
        else:
            log.debug('group id os not digit')
            wall = api.wall.get(domain=group_id,
                                filter='owner',
                                api_version=VK_API_VERSION)
    except VkAPIError as error_msg:
        log.info('group {} got api error: {}'.format(group_id, error_msg))
        return None

    return wall


def filter_out_copies(records):
    records_in_db = Record.objects.all()
    for record in records:
        for record_in_db in records_in_db:
            if SequenceMatcher(None, record['text'], record_in_db.text).ratio() > MIN_STRING_MATCH_RATIO:
                records.remove(record)
                log.debug('delete record {} as copy'.format(record['id']))
                break
            # TODO проверка изображений на дубликаты
    return records


def filter_out_ads(records):
    for record in records:
        if record['marked_as_ads']:
            records.remove(record)
            log.debug('delete record {} as ad: marked as ad'.format(record['id']))
            continue

        if 'copy_history' in record:
            records.remove(record)
            log.debug('delete record {} as ad: got forward msg'.format(record['id']))
            continue

        phone_numbers_in_text = PhoneNumberMatcher(text=record['text'], region='RU')
        if phone_numbers_in_text:
            records.remove(record)
            log.debug('delete record {} as ad: got phone'.format(record['id']))
            continue

        urls_in_text = re.findall('https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', record['text'])
        if urls_in_text:
            records.remove(record)
            log.debug('delete record {} as ad: got url'.format(record['id']))
            continue

        emails_in_text = re.findall(r'[\w.-]+ @ [\w.-]+', record['text'])
        if emails_in_text:
            records.remove(record)
            log.debug('delete record {} as ad: got email'.format(record['id']))
    return records


def filter_with_custom_filters(custom_filters, records):
    for custom_filter in custom_filters:
        for record in records:
            if custom_filter.min_quantity_of_line_breaks:
                if len(record['text'].splitlines()) < custom_filter.min_quantity_of_line_breaks:
                    records.remove(record)
                    log.debug('delete record {} because of min_quantity_of_line_breaks filter'.format(record['id']))
                    continue

            if custom_filter.min_text_length:
                if len(record['text']) < custom_filter.min_text_length:
                    records.remove(record)
                    log.debug('delete record {} because of min_text_length filter'.format(record['id']))
                    continue

            if custom_filter.min_quantity_of_videos:
                number_of_videos = len([item for item in record['attachments'] if item['type'] == 'video'])
                if number_of_videos < custom_filter.min_quantity_of_videos:
                    records.remove(record)
                    log.debug('delete record {} because of min_quantity_of_videos filter'.format(record['id']))
                    continue

            if custom_filter.min_quantity_of_images:
                number_of_images = len([item for item in record['attachments'] if item['type'] == 'photo'])
                if number_of_images < custom_filter.min_quantity_of_images:
                    records.remove(record)
                    log.debug('delete record {} because of min_quantity_of_images filter'.format(record['id']))
                    continue

            if custom_filter.min_quantity_of_gifs:
                number_of_gifs = len([item for item in record['attachments'] if item['type'] == 'doc' and
                                                                                item['doc']['ext'] == 'gif'])
                if number_of_gifs < custom_filter.min_quantity_of_gifs:
                    records.remove(record)
                    log.debug('delete record {} because of min_quantity_of_gifs filter'.format(record['id']))
    return records


def find_url_of_biggest_image(image_dict):
    photos_keys = [key for key in image_dict if key.startswith('photo_')]
    key_of_max_size_photo = max(photos_keys, key=lambda x: int(x.split('_')[1]))
    return image_dict[key_of_max_size_photo]


def save_record_to_db(donor, record):
    obj, created = Record.objects.get_or_create(
        donor=donor,
        record_id=record['id'],
        defaults={
            'likes_count': record['likes']['count'],
            'reposts_count': record['reposts']['count'],
            'views_count': record['views']['count'],
            'text': record['text'],
            'post_in_donor_date': record['date'],
            'add_to_db_date': datetime.datetime.now()
        }
    )
    if created:
        if 'attachments' in record:
            if any('video' in d for d in record['attachments']):
                videos = [item for item in record['attachments'] if item['type'] == 'video']
                for video in videos:
                    Video.objects.create(
                        record=obj,
                        owner_id=video['video']['owner_id'],
                        video_id=video['video']['id']
                    )

            if any('doc' in d for d in record['attachments']):
                gifs = [item for item in record['attachments'] if item['type'] == 'doc' and item['doc']['ext'] == 'gif']
                for gif in gifs:
                    Image.objects.create(
                        record=obj,
                        url=gif['doc']['url']
                    )

            if any('photo' in d for d in record['attachments']):
                images = [item for item in record['attachments'] if item['type'] == 'photo']
                for image in images:
                    Image.objects.create(
                        record=obj,
                        url=find_url_of_biggest_image(image['photo'])
                    )
    return created


def rate_records(donor_id, records):
    """

    :param donor:
    :param records:
    :type donor_id: int
    :type records: list
    :return: None
    """
    log.info('start rating {} records'.format(len(records)))

    default_timedelta = 3600
    factor = 0.5

    for record in records:
        # TODO make one query with all records instead of one call each record
        record_obj = Record.objects.get(donor__id=donor_id, record_id=record['id'])

        delta_likes = record['likes']['count'] - record_obj.likes_count
        delta_reposts = record['reposts']['count'] - record_obj.reposts_count
        delta_views = record['views']['count'] - record_obj.views_count

        resulting_rate = (delta_reposts/delta_likes + delta_likes/delta_views)*default_timedelta*factor
        record_obj.rate = int(resulting_rate)

        log.info('record {} in group {} rated {} with deltas likes: {}, reposts: {}, views:{}'.format(
            record['id'],
            donor_id,
            resulting_rate,
            delta_likes,
            delta_reposts,
            delta_views
        ))

        record_obj.save()


def main():
    log.info('start main scrapper')

    tokens = [acc.app_service_token for acc in User.objects.filter(app_service_token__isnull=False, group=None)]
    log.debug('working with {} tokens: {}'.format(len(tokens), tokens))

    donors = Donor.objects.filter(is_involved=True)
    log.debug('got {} active donors'.format(len(donors)))

    accounts_with_donors = distribute_donors_between_accounts(donors, tokens)
    log.info('got {} accounts with donors: {}'.format(len(accounts_with_donors), accounts_with_donors))

    for account in accounts_with_donors:
        if not account['donors']:
            log.info('account {} does not have any donor'.format(account))
            continue

        api = create_vk_api_using_service_token(account['token'])
        if not api:
            continue

        for donor in account['donors']:
            wall = get_wall(api, donor.id)
            if not wall:
                continue

            all_records = wall['items']

            log.debug('got {} records in donor <{}>'.format(len(all_records), donor.id))

            records = [record for record in all_records
                       if not Record.objects.filter(record_id=record['id']).first()]

            existing_records = list(set(all_records) - set(records))
            log.debug('got {} existing records'.format(len(existing_records)))

            non_rated_records = [record for record in existing_records
                                 if Record.objects.filter(record_id=record['id'], rate__isnull=True)]
            rate_records(donor.id, non_rated_records)

            records = filter_out_ads(records)

            custom_filters = donor.filters.all()
            if custom_filters:
                log.debug('got {} custom filters'.format(len(custom_filters)))
                records = filter_with_custom_filters(custom_filters, records)

            records = filter_out_copies(records)

            for record in records:
                save_record_to_db(donor, record)
                log.info('saved {} records'.format(len(records)))


if __name__ == '__main__':
    main()
