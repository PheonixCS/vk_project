#

# FIXME do not forget to remove all comments

import logging
import os
from pprint import pprint
import requests

# from constance import config

# log = logging.getLogger('services.tmdb')

API_KEY = 'ae02331036965fc7655049172b0247d0'
API_URL = 'https://api.themoviedb.org/3'
SEARCH_START_DATE = '1998-01-01'
IMAGE_URL = 'https://image.tmdb.org/t/p/original'
YOUTUBE_URL = 'https://www.youtube.com/watch?v='


def send_request_to_api(path, **kwargs):
    payload = {
        'api_key': API_KEY,
    }
    response = requests.get(f'{API_URL}{path}', params={**payload, **kwargs})
    if response.status_code == 200:
        return response.json()
    else:
        # TODO добавить логи
        pass


def discover_movies():
    total_pages = send_request_to_api(path='/discover/movie',
                                      **{'page': 1,
                                         'primary_release_date.gte': SEARCH_START_DATE,
                                         'language': 'ru-RU'}
                                      )['total_pages']

    for page_number in range(1, total_pages):
        movies = send_request_to_api(path='/discover/movie',
                                     **{'page': page_number,
                                        'primary_release_date.gte': SEARCH_START_DATE,
                                        'language': 'ru-RU'}
                                     )['results']

        for movie in movies:
            details = send_request_to_api(path=f'/movie/{movie["id"]}',
                                          **{'language': 'ru-RU',
                                             'append_to_response': 'videos,images',
                                             'include_image_language': 'null'}
                                          )
            yield {
                'title': details['title'],
                'rating': details['vote_average'],
                'release_date': details['release_date'],
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


if __name__ == '__main__':
    for movie in discover_movies():
        pprint(movie)
        break