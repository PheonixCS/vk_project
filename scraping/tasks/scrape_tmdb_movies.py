import logging
from datetime import datetime

from celery import shared_task
from constance import config

from scraping.core.scraper import save_movie_to_db
from services.themoviedb.wrapper import discover_movies

log = logging.getLogger('scraping.scheduled')


@shared_task
def scrape_tmdb_movies():
    if config.TMDB_SCRAPING_ENABLED:
        log.debug('run scrape_tmdb_movies')
        now_year = datetime.year
        for movie in discover_movies(end_year=now_year):
            save_movie_to_db(movie)
