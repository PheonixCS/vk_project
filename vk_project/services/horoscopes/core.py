#
import logging
import random
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

log = logging.getLogger('services.horoscopes')


class HoroscopesPage:
    SIGNS = [
            'arises',  # Овен
            'taurus',  # Телец
            'gemini',  # Близнецы
            'cancer',  # Рак
            'leo',  # Лев
            'virgo',  # Дева
            'libra',  # Весы
            'scorpio',  # Скорпион
            'sagittarius',  # Стрелец
            'capricorn',  # Козерог
            'aquarius',  # Водолеи
            'pisces'  # Рыбы
        ]

    def __init__(self, host):
        self.host = host
        self.signs_map = {}
        self.text_locator = ''
        self.parser = 'html.parser'

        self._headers = {
            'User-Agent': self.update_user_agent()
        }

    def parse(self, by_selector=False) -> dict:
        log.info(f'started parsing {self.host}')
        result = {}

        for sign in self.signs_map.items():
            url = urljoin(self.host, sign[1])

            try:
                response = requests.get(url, headers=self._headers)
                response.raise_for_status()
            except requests.exceptions.HTTPError as error:
                log.warning(f'Http error while parsing horoscopes, {url}, {error}')
                continue
            except requests.exceptions.Timeout as error:
                log.warning(f'Timeout while parsing horoscopes, {url}, {error}')
                continue
            except requests.exceptions.ConnectionError as error:
                log.warning(f'Connection error while parsing horoscopes, {url}, {error}')
                continue
            except requests.exceptions.RequestException as error:
                log.warning(f'Some requests error while parsing horoscopes, {url}, {error}')
                continue

            text = self._collect_data(response.text, by_selector=by_selector)

            if not text:
                log.warning(f'Could not find data, {url}, locator: {self.text_locator}')
                continue
            else:
                result.update({sign[0]: text})  # append sign name and horoscope text

        if len(result) < len(self.signs_map):
            log.warning('saved not all horoscopes signs!')

        if not result:
            log.info(f'got no horoscopes for {self.host}')
            raise Exception('No results found while parsing horoscopes')

        log.info(f'finish parsing {self.host}')
        return result

    def _collect_data(self, page_text, by_selector=False):
        soup = BeautifulSoup(page_text, self.parser)

        if by_selector:
            node = soup.select_one(self.text_locator)
            return node.text
        else:
            try:
                node = soup.findAll(self.text_locator)
            except Exception:
                log.warning('parsing exception', exc_info=True)
                return None

            if node:
                text = ''
                for child in node:
                    text += ''.join(child.findAll(text=True))
                return text
            else:
                return None

    @staticmethod
    def update_user_agent():
        list_of_agents = [
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.3 Safari/534.24'
        ]

        return random.choice(list_of_agents)

    @classmethod
    def get_signs(cls):
        return cls.SIGNS
