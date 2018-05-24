import datetime
import re
from difflib import SequenceMatcher
import logging

import vk_requests
from vk_requests.exceptions import VkAPIError
from phonenumbers import PhoneNumberMatcher

from posting.models import User, ServiceToken
from scraping.models import Donor, Record, Image, Gif, Video, Audio
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
        log.warning('token {} got api error: {}'.format(token, error_msg))
        return None

    return api


def get_wall(api, group_id, count=25):
    log.debug('get_wall api called for group {}'.format(group_id))

    try:
        if group_id.isdigit():
            log.debug('group id is digit')
            wall = api.wall.get(owner_id='-{}'.format(group_id),
                                filter='owner',
                                api_version=VK_API_VERSION,
                                count=count)
        else:
            log.debug('group id os not digit')
            wall = api.wall.get(domain=group_id,
                                filter='owner',
                                api_version=VK_API_VERSION,
                                count=count)
    except VkAPIError as error_msg:
        log.warning('group {} got api error: {}'.format(group_id, error_msg))
        return None

    return wall


def get_wall_by_post_id(api, group_id, posts_ids):
    log.debug('get_wall_by_post_id api called for group {}'.format(group_id))

    posts = ['-{}_{}'.format(group_id, post) for post in posts_ids]
    try:
        all_non_rated = api.wall.getById(posts=posts)
    except VkAPIError as error_msg:
        log.warning('group {} got api error while : {}'.format(group_id, error_msg))
        return None

    return all_non_rated


def filter_out_copies(records):
    log.info('filter_out_copies called')
    records_in_db = Record.objects.all()

    if not records_in_db:
        log.info('no records in db')
        return records

    filtered_records = list()

    for record in records:
        if any(record_in_db for record_in_db in records_in_db if
               SequenceMatcher(None, record['text'], record_in_db.text).ratio() < MIN_STRING_MATCH_RATIO):
            filtered_records.append(record)
        else:
            log.debug('record {} was filtered'.format(record['id']))

    # filtered_records = [record for record in records if any(record_in_db for record_in_db in records_in_db if
    #                                                         SequenceMatcher(None,
    #                                                                         record['text'],
    #                                                                         record_in_db.text).ratio() < MIN_STRING_MATCH_RATIO)]
    # TODO проверка изображений на дубликаты
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
    if re.findall('https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', item['text']):
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


def filter_out_ads(records):
    log.info('filter_out_ads called')
    filters = (
        marked_as_ads_filter,
        copy_history_filter,
        phone_numbers_filter,
        urls_filter,
        email_filter,
        article_filter
    )
    filtered_records = [record for record in records if all(filter(record) for filter in filters)]
    return filtered_records


def min_quantity_of_line_breaks_filter(item, custom_filter):
    if len(item['text'].splitlines()) < custom_filter.min_quantity_of_line_breaks:
        log.debug('delete {} because of custom filter: min_quantity_of_line_breaks'.format(item['id']))
        return False
    return True


def min_text_length_filter(item, custom_filter):
    if len(item['text']) < custom_filter.min_text_length:
        log.debug('delete {} because of custom filter: min_text_length'.format(item['id']))
        return False
    return True


def min_quantity_of_videos_filter(item, custom_filter):
    number_of_videos = len([attachment for attachment in item['attachments'] if attachment['type'] == 'video'])
    if number_of_videos < custom_filter.min_quantity_of_videos:
        log.debug('delete {} because of custom filter: min_quantity_of_videos'.format(item['id']))
        return False
    return True


def min_quantity_of_images_filter(item, custom_filter):
    number_of_images = len([attachment for attachment in item['attachments'] if attachment['type'] == 'photo'])
    if number_of_images < custom_filter.min_quantity_of_images:
        log.debug('delete {} because of custom filter: min_quantity_of_images'.format(item['id']))
        return False
    return True


def min_quantity_of_gifs_filter(item, custom_filter):
    number_of_gifs = len([attachment for attachment in item['attachments'] if attachment['type'] == 'doc' and
                          attachment['doc']['ext'] == 'gif'])
    if number_of_gifs < custom_filter.min_quantity_of_gifs:
        log.debug('delete {} because of custom filter: min_quantity_of_gifs'.format(item['id']))
        return False
    return True


def min_quantity_of_audios_filter(item, custom_filter):
    number_of_audios = len([attachment for attachment in item['attachments'] if attachment['type'] == 'audio'])
    if number_of_audios < custom_filter.min_quantity_of_audios:
        log.debug('delete {} because of custom filter: min_quantity_of_audios'.format(item['id']))
        return False
    return True


def filter_with_custom_filters(custom_filters, records):
    filtered_records = list(records)
    for custom_filter in custom_filters:
        filters = tuple()
        if custom_filter.min_quantity_of_line_breaks:
            filters += (min_quantity_of_line_breaks_filter,)

        if custom_filter.min_text_length:
            filters += (min_text_length_filter,)

        if custom_filter.min_quantity_of_videos:
            filters += (min_quantity_of_videos_filter,)

        if custom_filter.min_quantity_of_images:
            filters += (min_quantity_of_images_filter,)

        if custom_filter.min_quantity_of_gifs:
            filters += (min_quantity_of_gifs_filter,)

        if custom_filter.min_quantity_of_audios:
            filters += (min_quantity_of_audios_filter,)

        filtered_records = [record for record in filtered_records if
                            all(filter(record, custom_filter) for filter in filters)]

    return filtered_records


def find_url_of_biggest_image(image_dict):
    photos_keys = [key for key in image_dict if key.startswith('photo_')]
    key_of_max_size_photo = max(photos_keys, key=lambda x: int(x.split('_')[1]))
    return image_dict[key_of_max_size_photo]


def save_record_to_db(donor, record):
    log.info('save_record_to_db called')
    obj, created = Record.objects.get_or_create(
        donor=donor,
        record_id=record['id'],
        defaults={
            'likes_count': record['likes']['count'],
            'reposts_count': record['reposts']['count'],
            'views_count': record.get('views', dict()).get('count', 0),
            'text': record['text'],
            'post_in_donor_date': datetime.datetime.fromtimestamp(int(record['date'])).strftime('%Y-%m-%d %H:%M:%S')
        }
    )
    if created:
        log.info('record {} was in db, modifying'.format(record['id']))
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
                    Gif.objects.create(
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

            if any('audio' in d for d in record['attachments']):
                audios = [item for item in record['attachments'] if item['type'] == 'audio']
                for audio in audios:
                    Audio.objects.create(
                        record=obj,
                        owner_id=audio['audio']['owner_id'],
                        audio_id=audio['audio']['id']
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
        log.debug('rating {}'.format(record['id']))
        try:
            # FIXME add donor to query
            record_obj = Record.objects.get(record_id=record['id'])
        except:
            log.error('handling record error', exc_info=True)

        delta_likes = record['likes']['count'] - record_obj.likes_count
        delta_reposts = record['reposts']['count'] - record_obj.reposts_count
        delta_views = record.get('views', dict()).get('count', 0) - record_obj.views_count

        if delta_likes == 0 or delta_views == 0:
            log.info('record {} in group {} NOT rated with deltas likes: {}, reposts: {}, views:{}'.format(
                record['id'],
                donor_id,
                delta_likes,
                delta_reposts,
                delta_views
            ))
            continue

        resulting_rate = (delta_reposts / delta_likes + delta_likes / delta_views) * default_timedelta * factor
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

    tokens = [token.app_service_token for token in ServiceToken.objects.all()]
    log.info('working with {} tokens: {}'.format(len(tokens), tokens))

    donors = Donor.objects.filter(is_involved=True)
    log.info('got {} active donors'.format(len(donors)))

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
            # Scraping part

            wall = get_wall(api, donor.id)
            if not wall:
                continue

            # Fetch 20 records from donor wall.
            # That 20 records can content some useless information, adds and
            # information that we don't need.
            all_records = wall['items']
            log.debug('got {} records in donor <{}>'.format(len(all_records), donor.id))

            # now get records that we don't have in our db
            # FIXME add donor to query
            new_records = [record for record in all_records
                           if not Record.objects.filter(record_id=record['id']).first()]
            log.debug('got {} new records'.format(len(new_records)))

            # Filters
            if new_records:
                try:
                    new_records = filter_out_ads(new_records)
                    log.debug('got {} records'.format(len(new_records)))

                    custom_filters = donor.filters.all()
                    if custom_filters:
                        log.debug('got {} custom filters'.format(len(custom_filters)))
                        new_records = filter_with_custom_filters(custom_filters, new_records)
                        log.debug('got {} records'.format(len(new_records)))

                    new_records = filter_out_copies(new_records)

                    log.debug('got {} records after all filters'.format(len(new_records)))
                except:
                    log.error('error while filter', exc_info=True)
                    continue

            # Save it to db
            for record in new_records:
                try:
                    save_record_to_db(donor, record)
                except:
                    log.error('exception while saving in db', exc_info=True)
                    continue
                log.info('saved {} records'.format(len(new_records)))

            # Rating part
            # Get all non rated records from this api call
            # FIXME add donor to query
            non_rated_records = [record for record in all_records
                                 if Record.objects.filter(record_id=record['id'], rate__isnull=True)]

            if non_rated_records:
                try:
                    rate_records(donor.id, non_rated_records)
                except:
                    log.error('error while rating', exc_info=True)

            # FIXME add donor to query
            all_non_rated = Record.objects.filter(rate__isnull=True)

            if all_non_rated:
                if len(all_non_rated) > 100:
                    log.warning('too many non rated records!')
                    # TODO sort it by date, delete oldest
                    all_non_rated = all_non_rated[:100]

                # TODO make it clearer
                if donor.id.isdigit():
                    digit_id = donor.id
                else:
                    digit_id = new_records[0]['from_id']

                all_non_rated = [record.record_id for record in all_non_rated]

                all_non_rated = get_wall_by_post_id(api, digit_id, all_non_rated)

                if not all_non_rated:
                    log.warning('got 0 unrated records from api')
                    continue

                try:
                    rate_records(donor.id, all_non_rated)
                except:
                    log.error('error while rating', exc_info=True)


if __name__ == '__main__':
    main()
