import logging
from datetime import datetime

from celery import shared_task
from constance import config

from scraping.core.scraper import save_movie_to_db
from services.themoviedb.wrapper import discover_movies

log = logging.getLogger('scraping.scheduled')


@shared_task
def scrap_new_movies():
    log.debug('scrap_new_movies called')

    now_year = datetime.utcnow().year
    years_offset = config.TMDB_NEW_MOVIES_OFFSET

    for movie in discover_movies(end_year=now_year, years_offset=years_offset):
        save_movie_to_db(movie)

    log.debug('scrap_new_movies finished')
