import logging
from datetime import datetime
from random import shuffle

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
        # raise Exception(f'TMDb API response: {response.status_code}\n URL: {response.url}')
        return {}
    return response.json()


def find_suitable_images(images):
    images_sizes = set(map(lambda x: (x['height'], x['width']), images))
    grouped_images = [[image for image in images if image['height'] in size and image['width'] in size]
                      for size in images_sizes]
    grouped_images = [group for group in grouped_images if not len(group) < 3]
    suitable_images = max(grouped_images, key=lambda x: (x[0]['height'], x[0]['width']))
    shuffle(suitable_images)
    return [f'{IMAGE_URL}{image["file_path"]}' for image in suitable_images[:3]]


def discover_movies():
    log.debug('discover_movies called')

    start_year = config.TMDB_SEARCH_START_YEAR
    min_average_rating = 6.0

    for year in range(start_year, datetime.now().year+1):
        total_pages = send_request_to_api(path='/discover/movie',
                                          **{'page': 1,
                                             'primary_release_year': year,
                                             'vote_average.gte': min_average_rating,
                                             'language': 'ru-RU'}
                                          )['total_pages']
        if not total_pages:
            log.error('total_pages is empty')
            continue
        log.debug(f'got {total_pages} total pages in the {year} year')

        for page_number in range(1, total_pages):
            log.debug(f'working with {page_number} page')

            movies = send_request_to_api(path='/discover/movie',
                                         **{'page': page_number,
                                            'primary_release_year': year,
                                            'vote_average.gte': min_average_rating,
                                            'language': 'ru-RU'}
                                         )['results']

            if not movies:
                log.error('movies is empty')
                continue

            for movie in movies:
                log.debug(f'working with {movie["id"]} movie')

                details = send_request_to_api(path=f'/movie/{movie["id"]}',
                                              **{'language': 'ru-RU',
                                                 'append_to_response': 'videos,images',
                                                 'include_image_language': 'null'}
                                              )
                if not details:
                    log.error('details is empty')
                    continue

                countries = [country.get('iso_3166_1', 'US') for country in details.get('production_countries', [])]
                if 'IN' in countries:
                    continue

                frames = [frame for frame in details.get('images', {}).get('backdrops', []) if not frame['iso_639_1']]
                images = find_suitable_images(frames)
                if not images:
                    continue

                yield {
                    'title': details.get('title', ''),
                    'rating': details.get('vote_average', min_average_rating),
                    'release_year': datetime.strptime(details.get('release_date', start_year), '%Y-%m-%d').year,
                    'country': countries[0],
                    'genres': [genre.get('name') for genre in details.get('genres', [])],
                    'runtime': details.get('runtime', 120),
                    'trailers': [(video.get('size'), f'{YOUTUBE_URL}{video.get("key")}')
                                 for video in details.get('videos', {}).get('results', [])
                                 if video.get('type', '') == 'Trailer' and video.get('site', '') == 'YouTube'],
                    'overview': details.get('overview', ''),
                    'poster': f'{IMAGE_URL}{details.get("poster_path")}',
                    'images': images,
                }

    log.debug('discover_movies done')
