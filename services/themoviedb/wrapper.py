#

# FIXME do not forget to remove all comments

import logging
import os
import pprint

#from constance import config
from tmdbv3api import TMDb, Discover

#log = logging.getLogger('services.tmdb')


class APIKeyMissingError(Exception):
    pass


def get_api_key():
    if config.TMDB_KEY:
        return config.TMDB_KEY
    elif os.environ.get('TMDB_KEY'):
        return os.environ.get('TMDB_KEY')
    else:
        raise APIKeyMissingError('Cannot find api key')


def initialize_api():
    tmdb = TMDb()
    tmdb.api_key = ''  # get_api_key()


def get_most_popular_films_ids():
    discover = Discover()

    movie = discover.discover_movies({
        'primary_release_date.gte': '1998-01-01'
    })

    print(len(movie))

    return movie[:10]


if __name__ == '__main__':
    initialize_api()

    for film in get_most_popular_films_ids():
        print(film.title)
