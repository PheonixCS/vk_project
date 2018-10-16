from posting.models import Group
from scraping.core.horoscopes import fetch_zodiac_sign


def fetch_date_from_horoscope_text(raw_text):
    return raw_text.split('\n')[0].split(', ')[0]


def generate_special_group_reference(horoscope_text):
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

    special_group_zodiac_zign = fetch_zodiac_sign(horoscope_text).capitalize()
    special_group_id = Group.objects.filter(name=special_group_zodiac_zign).first().domain_or_id
    horoscope_date = fetch_date_from_horoscope_text(horoscope_text)
    return f'[club{special_group_id}|' \
           f'Гороскоп для {replace_map[special_group_zodiac_zign]}] ' \
           f'на {horoscope_date}'
