import datetime
import re
from difflib import SequenceMatcher
import logging

import vk_requests
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


def create_vk_api_using_service_token(token, api_version):
    return vk_requests.create_api(service_token=token, api_version=api_version)


def get_wall(api, group_id):
    # TODO обработка ошибок api
    if group_id.isdigit():
        wall = api.wall.get(owner_id='-{}'.format(group_id),
                            filter='owner',
                            api_version=VK_API_VERSION)
    else:
        wall = api.wall.get(domain=group_id,
                            filter='owner',
                            api_version=VK_API_VERSION)
    return wall


def filter_out_copies(records):
    records_in_db = Record.objects.all()
    for record in records:
        for record_in_db in records_in_db:
            if SequenceMatcher(None, record['text'], record_in_db.text).ratio() > MIN_STRING_MATCH_RATIO:
                records.remove(record)
                break
            # TODO проверка изображений на дубликаты
    return records


def filter_out_ads(records):
    for record in records:
        if record['marked_as_ads']:
            records.remove(record)
            continue

        if 'copy_history' in record:
            records.remove(record)
            continue

        phone_numbers_in_text = PhoneNumberMatcher(text=record['text'], region='RU')
        if phone_numbers_in_text:
            records.remove(record)
            continue

        urls_in_text = re.findall('https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', record['text'])
        if urls_in_text:
            records.remove(record)
            continue

        emails_in_text = re.findall(r'[\w.-]+ @ [\w.-]+', record['text'])
        if emails_in_text:
            records.remove(record)
    return records


def filter_with_custom_filters(custom_filters, records):
    for custom_filter in custom_filters:
        for record in records:
            if custom_filter.min_quantity_of_line_breaks:
                if len(record['text'].splitlines()) < custom_filter.min_quantity_of_line_breaks:
                    records.remove(record)
                    continue

            if custom_filter.min_text_length:
                if len(record['text']) < custom_filter.min_text_length:
                    records.remove(record)
                    continue

            if custom_filter.min_quantity_of_videos:
                number_of_videos = len([item for item in record['attachments'] if item['type'] == 'video'])
                if number_of_videos < custom_filter.min_quantity_of_videos:
                    records.remove(record)
                    continue

            if custom_filter.min_quantity_of_images:
                number_of_images = len([item for item in record['attachments'] if item['type'] == 'photo'])
                if number_of_images < custom_filter.min_quantity_of_images:
                    records.remove(record)
                    continue

            if custom_filter.min_quantity_of_gifs:
                number_of_gifs = len([item for item in record['attachments'] if item['type'] == 'doc' and
                                                                                item['doc']['ext'] == 'gif'])
                if number_of_gifs < custom_filter.min_quantity_of_gifs:
                    records.remove(record)
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


def main():
    log.info('start main scrapper')

    tokens = [acc.app_service_token for acc in User.objects.filter(app_service_token__isnull=False, group=None)]

    donors = Donor.objects.filter(is_involved=True)

    accounts_with_donors = distribute_donors_between_accounts(donors, tokens)

    for account in accounts_with_donors:
        if not account['donors']:
            continue

        api = create_vk_api_using_service_token(account['token'], VK_API_VERSION)

        for donor in account['donors']:
            records = get_wall(api, donor.id)['items']

            records = [record for record in records if not Record.objects.filter(record_id=record['id']).first()]

            records = filter_out_ads(records)

            custom_filters = donor.filters.all()
            if custom_filters:
                records = filter_with_custom_filters(custom_filters, records)

            records = filter_out_copies(records)

            for record in records:
                save_record_to_db(donor, record)


if __name__ == '__main__':
    main()
