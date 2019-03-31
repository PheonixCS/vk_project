#
import logging
from datetime import datetime, timedelta

from celery import shared_task
from constance import config
from django.db.models import Sum
from django.utils import timezone

from posting.core.poster import get_movies_rating_intervals
from scraping.core.scraper import main, save_movie_to_db, save_structured_records
from scraping.core.vk_helper import get_records_info
from scraping.models import Record, Horoscope, Trailer, Movie, Donor
from services.themoviedb.wrapper import discover_movies
from services.youtube.core import download_trailer
from scraping.core.helpers import extract_records_per_donor


log = logging.getLogger('scraping.scheduled')


@shared_task
def run_scraper():
    main()


@shared_task
def scrape_tmdb_movies():
    if config.TMDB_SCRAPING_ENABLED:
        now_year = datetime.year
        for movie in discover_movies(end_year=now_year):
            save_movie_to_db(movie)


@shared_task
def delete_oldest():
    log.debug('start deleting records')

    max_count = config.COMMON_RECORDS_COUNT_FOR_DONOR

    donors = Donor.objects.filter(
        is_involved=True
    )

    for donor in donors.iterator():
        records_number = Record.objects.filter(donor=donor).count()

        if records_number > max_count:
            records_to_delete_number = records_number - max_count

            all_records = Record.objects.filter(donor=donor).order_by('post_in_donor_date')
            ids_to_delete = all_records[:records_to_delete_number].values_list('id', flat=True)
            records_to_delete = all_records.filter(pk__in=ids_to_delete)

            number_of_records, extended = records_to_delete.delete()
            log.debug(f'deleted {number_of_records} records for group {donor.id}')

    log.debug('finish deleting records')


@shared_task
def delete_old_horoscope_records():
    hours = config.OLD_HOROSCOPES_HOURS
    time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    log.debug('start deleting horoscope records older than {}'.format(time_threshold))

    number_of_records, extended = Horoscope.objects.filter(add_to_db_date__lt=time_threshold).delete()
    log.debug('deleted {} records'.format(number_of_records))


@shared_task
def download_youtube_trailers():
    log.debug('download_youtube_trailers start analyzing')

    rating_intervals = get_movies_rating_intervals()

    for rating_interval in rating_intervals:
        # check if we got movie with this suitable rating and downloaded trailer
        downloaded_movie = Movie.objects.filter(rating__in=rating_interval,
                                                trailers__status=Trailer.DOWNLOADED_STATUS).first()
        if downloaded_movie:
            continue

        # search for new movie with appropriate interval and new trailer
        movie = Movie.objects.filter(rating__in=rating_interval,
                                     trailers__status=Trailer.NEW_STATUS).first()

        if movie:
            log.debug('work with new movie')
            trailer = movie.trailers.filter(status=Trailer.NEW_STATUS).first()

            if trailer:
                trailer.status = Trailer.PENDING_STATUS
                trailer.save(update_fields=['status'])

                downloaded_trailer_path = download_trailer(trailer.url)

                if downloaded_trailer_path:
                    trailer.status = Trailer.DOWNLOADED_STATUS
                    trailer.file_path = downloaded_trailer_path

                    trailer.save(update_fields=['status', 'file_path'])
                else:
                    trailer.status = Trailer.FAILED_STATUS
                    trailer.save(update_fields=['status'])

        log.debug('finish downloading trailers')


@shared_task
def scrap_new_movies():
    log.debug('scrap_new_movies called')

    now_year = datetime.utcnow().year
    years_offset = config.TMDB_NEW_MOVIES_OFFSET

    for movie in discover_movies(end_year=now_year, years_offset=years_offset):
        save_movie_to_db(movie)

    log.debug('scrap_new_movies finished')


@shared_task
def set_donors_average_view():
    log.debug('set_donors_average_view started')

    required_count = config.COMMON_RECORDS_COUNT_FOR_DONOR
    donors = Donor.objects.filter(is_involved=True, is_banned=False)

    for donor in donors:
        if donor.records.count() < required_count:
            log.info(f'group {donor.id} has not enough records, skip')
            continue
        else:
            all_records = Record.objects.filter(donor=donor).order_by('-post_in_donor_date')[:required_count]
            views_count = all_records.aggregate(Sum('views_count')).get('views_count__sum')
            donor.average_views_number = views_count/required_count
            donor.save(update_fields=['average_views_number'])

    log.debug('set_donors_average_view finished')


@shared_task
def rate_new_posts() -> None:
    log.debug('rating started')
    # TODO timedelta to config
    threshold = datetime.now(tz=timezone.utc) - timedelta(hours=2)

    new_records = Record.objects.filter(status=Record.NEW, post_in_donor_date__lte=threshold)

    if new_records:
        records_info = get_records_info(new_records)
        structured_records = extract_records_per_donor(records_info)
        save_structured_records(structured_records)

    log.debug('rating finished')
