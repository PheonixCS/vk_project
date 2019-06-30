import datetime
import logging

from django.utils import timezone

from posting.models import ServiceToken
from scraping.core.filters import (
    filter_with_custom_filters,
    filter_out_ads,
    filter_out_copies,
    filter_out_records_with_unsuitable_attachments,
    filter_out_records_with_small_images,
)
from scraping.core.helpers import (
    distribute_donors_between_accounts,
    find_url_of_biggest_image,
    is_donor_out_of_date,
    find_newest_record,
)
from scraping.models import (
    Donor,
    Record,
    Image,
    Gif,
    Video,
    Audio,
    Movie,
    Genre,
    Trailer,
    Frame
)
from services.vk.core import create_vk_api_using_service_token
from services.vk.vars import GROUP_IS_BANNED
from services.vk.wall import get_wall
from scraping.core.scraping_history import save_filter_stats

log = logging.getLogger('scraping.scraper')


def save_record_to_db(donor, record):
    log.info('save_record_to_db called')
    obj, created = Record.objects.get_or_create(
        donor=donor,
        record_id=record['id'],
        defaults={
            'text': record['text'],
            'post_in_donor_date': datetime.datetime.fromtimestamp(int(record['date']), tz=timezone.utc).strftime(
                '%Y-%m-%d %H:%M:%S')
        }
    )
    if created:
        log.info('record {} created'.format(record['id']))
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
                        audio_id=audio['audio']['id'],
                        artist=audio['audio']['artist'],
                        genre=str(audio['audio'].get('genre_id', ''))
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
        for trailer in movie['trailers']:
            Trailer.objects.create(
                movie=obj,
                url=trailer
            )
        for frame in movie['images']:
            Frame.objects.create(
                movie=obj,
                url=frame
            )
    return created


def main():
    log.info('start main scrapper')

    tokens = [token.app_service_token for token in ServiceToken.objects.all()]
    log.info('working with {} tokens: {}'.format(len(tokens), tokens))

    donors = Donor.objects.filter(is_involved=True, ban_reason__isnull=True)
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

            wall, error_reason = get_wall(api, donor.id)
            if not wall:
                if error_reason == GROUP_IS_BANNED:
                    donor.ban(reason=donor.DISABLED)
                continue

            newest_record = find_newest_record(wall['items'])
            if is_donor_out_of_date(newest_record['date']):
                donor.ban(reason=donor.OLD)
                continue

            new_records = exclude_old_records(donor, wall)

            try:
                filtered_new_records = filter_records(donor, new_records)
            except:
                log.error('error while filter', exc_info=True)
                continue

            # Save records to db
            for record in filtered_new_records:
                save_record_to_db(donor, record)
            log.info('saved {} records in group {}'.format(len(filtered_new_records), donor.id))


# TODO need tests
def filter_records(donor, records):
    origin = len(records)
    records = filter_out_ads(records)
    save_filter_stats(donor, 'ads', origin-len(records))

    origin = len(records)
    records = filter_out_records_with_small_images(records)
    save_filter_stats(donor, 'small_images', origin - len(records))

    custom_filters = donor.filters.all()
    if custom_filters:
        log.debug('got {} custom filters'.format(len(custom_filters)))
        origin = len(records)
        records = filter_with_custom_filters(records, custom_filters)
        save_filter_stats(donor, 'custom_filters', origin - len(records))

    origin = len(records)
    records = filter_out_copies(records)
    save_filter_stats(donor, 'copies', origin - len(records))

    origin = len(records)
    records = filter_out_records_with_unsuitable_attachments(records)
    save_filter_stats(donor, 'bad attachments', origin - len(records))

    log.debug('got {} records after all filters in donor {}'.format(len(records), donor.id))
    return records


# TODO need tests
def exclude_old_records(donor, wall):
    all_records = wall['items']
    log.debug('got {} records in donor <{}>'.format(len(all_records), donor.id))

    # now get records that we don't have in our db
    # new_records = [record for record in all_records
    #                if not Record.objects.filter(record_id=record['id'], donor_id=donor.id).first()]

    donor_record_ids = Record.objects.filter(donor=donor).values_list('record_id', flat=True)
    new_records = [record for record in all_records if not record['id'] in donor_record_ids]

    log.debug('got {} new records in donor {}'.format(len(new_records), donor.id))

    return new_records


def update_structured_records(records: dict) -> None:
    log.debug('update_structured_records called')
    fields = ['rate', 'views_count', 'likes_count', 'reposts_count', 'females_count',
              'males_count', 'unknown_count', 'males_females_ratio', 'status']

    for donor_id in records.keys():
        fresh_records = records[donor_id]
        donor_records_ids = [record['id'] for record in fresh_records]

        try:
            donor = Donor.objects.get(id=str(donor_id))
        except Donor.DoesNotExist:
            log.info(f'not existing donor {donor_id} with {len(fresh_records)} records', exc_info=True)
            continue

        records_in_db = Record.objects.filter(record_id__in=donor_records_ids, donor=donor)

        for record in records_in_db:
            fresh_record = [item for item in fresh_records if item['id'] == record.record_id].pop()

            record.views_count = fresh_record.get('views', {}).get('count', 0)
            record.likes_count = fresh_record.get('likes', {}).get('count', 0)
            record.reposts_count = fresh_record.get('reposts', {}).get('count', 0)
            record.unknown_count = fresh_record.get('unknown_count', 0)
            record.males_count = fresh_record.get('males_count', 1)
            record.females_count = fresh_record.get('females_count', 1)
            record.males_females_ratio = fresh_record.get('males_females_ratio', 1)

            if donor.average_views_number is None:  # I don't know why without "is None" it doesn't work as I want
                log.info(f'Donor {donor_id},{donor.name} has not average views number, fallback')
                if 0 in (record.reposts_count, record.likes_count, record.views_count):
                    record.rate = 0
                else:
                    record.rate = (record.reposts_count / record.likes_count
                                   + record.likes_count / record.views_count) * 900
            else:
                record.rate = record.views_count / donor.average_views_number * 1000

            record.status = Record.READY
            record.save(update_fields=fields)
