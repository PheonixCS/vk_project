import datetime
import logging

from constance import config
from django.utils import timezone

from posting.models import ServiceToken, Group
from scraping.core.filters import (
    filter_with_custom_filters,
    filter_out_ads,
    filter_out_copies,
    filter_out_records_with_unsuitable_attachments,
    filter_out_records_with_small_images,
)
from scraping.core.helpers import distribute_donors_between_accounts, find_url_of_biggest_image
from scraping.core.horoscopes import find_horoscopes, fetch_zodiac_sign
from services.vk.stat import fetch_liked_user_ids, get_users_sex_by_ids
from services.vk.wall import get_wall, get_wall_by_post_id
from services.vk.core import create_vk_api_using_service_token
from scraping.models import Donor, Record, Image, Gif, Video, Audio, Horoscope, \
    Movie, Genre, Trailer, Frame

log = logging.getLogger('scraping.scraper')


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
            'post_in_donor_date': datetime.datetime.fromtimestamp(int(record['date']), tz=timezone.utc).strftime(
                '%Y-%m-%d %H:%M:%S')
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
                gifs = [item for item in record['attachments'] if item['type'] == 'doc' and item['doc']['ext'] == 'gif'
                        and item['doc']['owner_id'] > 0]
                for gif in gifs:
                    Gif.objects.create(
                        record=obj,
                        url=gif['doc']['url'],
                        owner_id=gif['doc']['owner_id'],
                        gif_id=gif['doc']['id'],
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


def save_movie_to_db(movie):
    log.info('save_movie_to_db called')
    obj, created = Movie.objects.get_or_create(
        title=movie['title'],
        release_year=movie['release_year'],
        runtime=movie['runtime'],
        defaults={
            'rating': movie['rating'],
            'overview': movie['overview'],
            'poster': movie['poster'],
            'production_country_code': movie['country']
        }
    )
    if created:
        for genre in movie['genres']:
            Genre.objects.create(
                movie=obj,
                name=genre
            )
        Trailer.objects.create(
            movie=obj,
            url=movie['trailer']
        )
        for frame in movie['images']:
            Frame.objects.create(
                movie=obj,
                url=frame
            )
    return created


def save_horoscope_record_to_db(group, record, zodiac_sign):
    log.info('save_horoscope_record_to_db called')
    obj, created = Horoscope.objects.get_or_create(
        group=group,
        zodiac_sign=zodiac_sign,
        post_in_donor_date=datetime.datetime.fromtimestamp(int(record['date']), tz=timezone.utc).strftime(
            '%Y-%m-%d %H:%M:%S'),
        defaults={
            'text': record['text'],
        }
    )
    if created:
        log.info('record {} was in db, modifying'.format(record['id']))
        if 'attachments' in record:
            if any('photo' in d for d in record['attachments']):
                images = [item for item in record['attachments'] if item['type'] == 'photo']
                for image in images:
                    obj.image_url = find_url_of_biggest_image(image['photo'])
                obj.save(update_fields=['image_url'])
    log.info('save_horoscope_record_to_db result: {}'.format(created))

    return created


def rate_records(donor_id, records):
    """

    :param donor_id:
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
            record_obj = Record.objects.get(record_id=record['id'], donor_id=donor_id)
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

        if delta_likes == 0 or delta_reposts == 0 or delta_views == 0:
            resulting_rate = 1  # consider that this is right minimum
        else:
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
            new_records = [record for record in all_records
                           if not Record.objects.filter(record_id=record['id'], donor_id=donor.id).first()]
            log.debug('got {} new records in donor {}'.format(len(new_records), donor.id))

            # Filters
            if new_records:
                try:
                    new_records = filter_out_ads(new_records)
                    log.debug('got {} records in donor {}'.format(len(new_records), donor.id))

                    new_records = filter_out_records_with_small_images(new_records)

                    custom_filters = donor.filters.all()
                    if custom_filters:
                        log.debug('got {} custom filters'.format(len(custom_filters)))
                        new_records = filter_with_custom_filters(custom_filters, new_records)
                        log.debug('got {} records in donor {}'.format(len(new_records), donor.id))

                    new_records = filter_out_copies(new_records)

                    new_records = filter_out_records_with_unsuitable_attachments(new_records)

                    log.debug('got {} records after all filters in donor {}'.format(len(new_records), donor.id))
                except:
                    log.error('error while filter', exc_info=True)
                    continue

            # Horoscopes
            horoscopes_donor_id = config.HOROSCOPES_DONOR_ID
            if horoscopes_donor_id in donor.id:
                log.debug('start scraping horoscope donor')
                horoscopes_records = find_horoscopes(new_records)
                log.debug('got {} horoscopes records'.format(len(horoscopes_records)))

                groups_with_horoscope_posting = Group.objects.filter(is_horoscopes=True)
                log.debug('got {} groups with active horoscope posting'.format(len(groups_with_horoscope_posting)))

                for horoscope_record in horoscopes_records:
                    new_records.remove(horoscope_record)

                    # Save horoscope to db
                    for group in groups_with_horoscope_posting:
                        record_zodiac_sign = fetch_zodiac_sign(horoscope_record.get('text').splitlines()[0])
                        group_zodiac_sign = fetch_zodiac_sign(group.name)
                        if group_zodiac_sign:
                            if not group_zodiac_sign == record_zodiac_sign:
                                continue

                        log.debug('saving horoscope record {} in db'.format(horoscope_record['id']))
                        save_horoscope_record_to_db(group, horoscope_record, record_zodiac_sign)
            log.debug('got {} records after deleting horoscopes posts in donor {}'.format(len(new_records),
                                                                                          donor.id))

            # Save records to db
            for record in new_records:
                save_record_to_db(donor, record)
            log.info('saved {} records in group {}'.format(len(new_records), donor.id))

            # Rating part
            # Get all non rated records from this api call
            non_rated_records = [record for record in all_records
                                 if Record.objects.filter(record_id=record['id'], rate__isnull=True, donor_id=donor.id)]

            if non_rated_records:
                try:
                    rate_records(donor.id, non_rated_records)
                    extract_records_sex(api, donor.id, non_rated_records)
                except:
                    log.error('error while rating', exc_info=True)

            all_non_rated = Record.objects.filter(rate__isnull=True, donor_id=donor.id)

            if all_non_rated:
                if len(all_non_rated) > 100:
                    log.warning('too many non rated records!')
                    # TODO sort it by date, delete oldest
                    all_non_rated = all_non_rated[:100]

                if donor.id.isdigit():
                    digit_id = donor.id
                else:
                    # TODO fix this
                    # digit_id = fetch_group_id(api, donor.id)
                    digit_id = donor.id

                all_non_rated = [record.record_id for record in all_non_rated]

                all_non_rated = get_wall_by_post_id(api, digit_id, all_non_rated)

                if not all_non_rated:
                    log.warning('got 0 unrated records from api')
                    continue

                rate_records(donor.id, all_non_rated)


def extract_records_sex(api, donor_id, records):
    log.debug('extract_records_sex called')
    for record in records:
        record_obj = Record.objects.get(record_id=record['id'], donor_id=donor_id)
        user_ids = fetch_liked_user_ids(api, donor_id, record['id'])
        sex_list = get_users_sex_by_ids(api, user_ids)

        females_count = sex_list.count(1)
        males_count = sex_list.count(2)

        males_females_ratio = males_count/females_count

        record_obj.females_count = females_count
        record_obj.males_count = males_count
        record_obj.unknown_count = sex_list.count(0)
        record_obj.males_females_ratio = males_females_ratio

        record_obj.save(update_fields=['females_count', 'males_count', 'unknown_count', 'males_females_ratio'])

    log.debug('extract_records_sex finished')
