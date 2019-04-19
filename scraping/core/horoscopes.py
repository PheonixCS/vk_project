#
import re


def fetch_zodiac_sign(text):
    zodiac_signs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева',
                    'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
    for zodiac_sign in zodiac_signs:
        if zodiac_sign.lower() in text.lower():
            return zodiac_sign.lower()
    return None


def find_horoscopes(records):
    horoscopes_records = []
    for record in records:
        text = record.get('text')
        if text:
            first_line = text.splitlines()[0]
        else:
            continue

        if fetch_zodiac_sign(first_line) and bool(re.search(r'\d', first_line)):
            horoscopes_records.append(record)

    return horoscopes_records


def horoscopes_translate(name, to_lang='ru'):
    signs_map = {
        'arises': 'овен',
        'taurus': 'телец',
        'gemini': 'близнецы',
        'cancer': 'рак',
        'leo': 'лев',
        'virgo': 'дева',
        'libra': 'весы',
        'scorpio': 'скорпион',
        'sagittarius': 'стрелец',
        'capricorn': 'козерог',
        'aquarius': 'водолеи',
        'pisces': 'рыбы'
    }

    if to_lang == 'en':
        signs_map = dict((v, k) for k, v in signs_map.items())

    return signs_map.get(name)
