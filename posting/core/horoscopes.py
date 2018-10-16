from scraping.core.horoscopes import fetch_zodiac_sign


def fetch_date_from_horoscope_text(raw_text):
    return raw_text.split('\n')[0].split(', ')[0]


def generate_special_group_reference(horoscope_text, group_id):
    replace_map = {
        'Овен': 'Овна',
        'Телец': 'Тельца',
        'Близнецы': 'Близнеца',
        'Рак': 'Рака',
        'Лев': 'Льва',
        'Дева': 'Девы',
        'Весы': 'Весов',
        'Скорпион': 'Скорпиона',
        'Стрелец': 'Стрельца',
        'Козерог': 'Козерога',
        'Водолей': 'Водолея',
        'Рыбы': 'Рыбы',
    }

    horoscope_date = fetch_date_from_horoscope_text(horoscope_text)
    return f'[club{group_id}|Гороскоп для {replace_map[fetch_zodiac_sign(horoscope_text)]}] на {horoscope_date}'
