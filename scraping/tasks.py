#
import logging
from datetime import datetime, timedelta

from celery import task
from constance import config
from django.utils import timezone

from posting.core.poster import get_movies_rating_intervals
from scraping.core.scraper import main, save_movie_to_db
from scraping.models import Record, Horoscope, Trailer, Movie
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


@task
def scrap_new_movies():
    log.debug('scrap_new_movies called')

    now_year = datetime.utcnow().year
    years_offset = config.TMDB_NEW_MOVIES_OFFSET

    for movie in discover_movies(end_year=now_year, years_offset=years_offset):
        save_movie_to_db(movie)

    log.debug('scrap_new_movies finished')
