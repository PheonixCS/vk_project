#
import logging
from datetime import datetime, timedelta

from celery import task
from constance import config
from django.utils import timezone
from random import choice

from posting.poster import get_movies_rating_intervals
from scraping.core.scraper import main, save_movie_to_db
from scraping.models import Record, Horoscope, Trailer
from services.themoviedb.wrapper import discover_movies
from services.youtube.core import download_trailer

log = logging.getLogger('scraping.scheduled')


@task
def run_scraper():
    main()


@task
def scrape_tmdb_movies():
    if config.TMDB_SCRAPING_ENABLED:
        now_year = datetime.year
        for movie in discover_movies(end_year=now_year):
            save_movie_to_db(movie)


@task
def delete_oldest():
    """
    Scheduled task for deleting records 24 hours old

    :return:
    """
    hours = config.OLD_RECORDS_HOURS
    time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    log.debug('start deleting records older than {}'.format(time_threshold))

    number_of_records, extended = Record.objects.filter(add_to_db_date__lt=time_threshold).delete()
    log.debug('deleted {} records'.format(number_of_records))


@task
def delete_old_horoscope_records():
    hours = config.OLD_HOROSCOPES_HOURS
    time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    log.debug('start deleting horoscope records older than {}'.format(time_threshold))

    number_of_records, extended = Horoscope.objects.filter(add_to_db_date__lt=time_threshold).delete()
    log.debug('deleted {} records'.format(number_of_records))


@task
def download_youtube_trailers():
    log.debug('download_youtube_trailers start analyzing')

    downloaded_trailers = Trailer.objects.filter(status=Trailer.DOWNLOADED_STATUS)
    downloaded_count = downloaded_trailers.count()

    rating_intervals = get_movies_rating_intervals()

    if downloaded_count < config.TMDB_MIN_TRAILERS_COUNT:
        log.debug('download_youtube_trailers start downloading')

        for trailer in downloaded_trailers:
            movie_rating_interval = [rating for interval in rating_intervals for rating in interval
                                     if trailer.movie.rating in interval]
            rating_intervals.remove(movie_rating_interval)

        for rating_interval in rating_intervals:
            trailers = Trailer.objects.filter(status=Trailer.NEW_STATUS,
                                              movie__rating__in=rating_interval)
            if trailers:
                trailer = choice(trailers)
            else:
                log.debug(f'got no trailers in {rating_interval} movie rating interval')
                continue

            trailer.status = Trailer.PENDING_STATUS
            trailer.save(update_fields=['status'])

            trailer_path = download_trailer(trailer.url)
            if not trailer_path:
                trailer.status = Trailer.FAILED_STATUS
                # TODO beware of endless loop
                download_youtube_trailers.delay()
                return
            trailer.file_path = trailer_path

            trailer.status = Trailer.DOWNLOADED_STATUS
            trailer.save(update_fields=['file_path', 'status'])

        log.debug('finish downloading trailer')


@task
def scrap_new_movies():
    log.debug('scrap_new_movies called')

    now_year = datetime.utcnow().year
    years_offset = config.TMDB_NEW_MOVIES_OFFSET

    for movie in discover_movies(end_year=now_year, years_offset=years_offset):
        save_movie_to_db(movie)

    log.debug('scrap_new_movies finished')
