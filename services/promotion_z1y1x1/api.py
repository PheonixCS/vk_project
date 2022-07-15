import logging
from typing import Optional

from constance import config
from requests import Session
from requests.exceptions import BaseHTTPError
import json

host = 'http://api.z1y1x1.ru'
create_endpoint = '/tasks/create'
status_endpoint = '/tasks/status'

log = logging.getLogger(__name__)


def create_new_task(post_url):
    session = Session()
    result = dict()

    url = host + create_endpoint
    token = config.X_TOKEN

    data = {
        'token': token,
        'content': post_url,
        'count': 30,
        'speed': 30
    }

    try:
        response = session.get(url, params=data)
        result = response.json()

    except BaseHTTPError as error:
        log.warning(f'Check status exception: {error}')

    except json.JSONDecodeError as error:
        log.warning(f'Check status exception: {error}')

    return result


def check_task_status(task_id) -> Optional[dict]:
    session = Session()
    result = dict()

    url = host + status_endpoint
    token = config.X_TOKEN

    data = {
        'token': token,
        'task': task_id,
    }

    try:
        response = session.get(url, params=data)
        result = response.json()

    except BaseHTTPError as error:
        log.warning(f'Check status exception: {error}')

    except json.JSONDecodeError as error:
        log.warning(f'Check status exception: {error}')

    return result
