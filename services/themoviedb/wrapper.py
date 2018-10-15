import logging
from datetime import datetime

import requests
from constance import config
from ratelimit import limits, sleep_and_retry

log = logging.getLogger('services.tmdb')

API_URL = 'https://api.themoviedb.org/3'
IMAGE_URL = 'https://image.tmdb.org/t/p/original'
SEARCH_START_YEAR = 1998
YOUTUBE_URL = 'https://www.youtube.com/watch?v='


@sleep_and_retry
@limits(calls=40, period=10)
def send_request_to_api(path, **kwargs):
    payload = {
        'api_key': config.TMDB_API_KEY,
    }
    response = requests.get(f'{API_URL}{path}', params={**payload, **kwargs})

    if response.status_code != 200:
        log.error(f'TMDb API response: {response.status_code}\n URL: {response.url}')
        raise Exception(f'TMDb API response: {response.status_code}\n URL: {response.url}')
    return response.json()


def discover_movies():
    log.debug('discover_movies called')

    for year in range(config.TMDB_SEARCH_START_YEAR, datetime.now().year):
        total_pages = send_request_to_api(path='/discover/movie',
                                          **{'page': 1,
                                             'primary_release_date.gte': year,
                                             'language': 'ru-RU'}
                                          )['total_pages']
        log.debug(f'got {total_pages} total pages in the {year} year')

        for page_number in range(1, total_pages):
            log.debug(f'working with {page_number} page')

            movies = send_request_to_api(path='/discover/movie',
                                         **{'page': page_number,
                                            'primary_release_year': year,
                                            'language': 'ru-RU'}
                                         )['results']

            for movie in movies:
                log.debug(f'working with {movie["id"]} movie')

                details = send_request_to_api(path=f'/movie/{movie["id"]}',
                                              **{'language': 'ru-RU',
                                                 'append_to_response': 'videos,images',
                                                 'include_image_language': 'null'}
                                              )
                yield {
                    'title': details['title'],
                    'rating': details['vote_average'],
                    'release_year': datetime.strptime(details['release_date'], '%Y-%m-%d').year,
                    'countries': [country['iso_3166_1'] for country in details['production_countries']],
                    'genres': [genre['name'] for genre in details['genres']],
                    'runtime': details['runtime'],
                    'trailers': [(video['size'], f'{YOUTUBE_URL}{video["key"]}') for video in details['videos']['results']
                                 if video['type'] == 'Trailer' and video['site'] == 'YouTube'],
                    'overview': details['overview'],
                    'poster': f'{IMAGE_URL}{details["poster_path"]}',
                    'images': [f'{IMAGE_URL}{frame["file_path"]}' for frame in details['images']['backdrops'] if
                               not frame['iso_639_1']],
                }

    log.debug('discover_movies done')
