#
import logging
from datetime import datetime, timedelta

from celery import task
from constance import config
from django.utils import timezone

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
        for movie in discover_movies():
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

    downloaded_count = Trailer.objects.filter(status=Trailer.DOWNLOADED_STATUS).count()

    if downloaded_count < config.TMDB_MIN_TRAILERS_COUNT:
        log.debug('download_youtube_trailers start downloading')

        trailer = Trailer.objects.random()

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



