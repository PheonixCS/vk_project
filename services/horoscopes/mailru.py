# special class for mail ru horoscopes

from .core import HoroscopesPage


class MailRuHoroscopes(HoroscopesPage):
    def __init__(self):
        super().__init__('https://horo.mail.ru')

        self.signs_map = {
            'arises': '/prediction/aries/tomorrow/',  # Овен
            'taurus': '/prediction/taurus/tomorrow/',  # Телец
            'gemini': '/prediction/gemini/tomorrow/',  # Близнецы
            'cancer': '/prediction/cancer/tomorrow/',  # Рак
            'leo': '/prediction/leo/tomorrow/',  # Лев
            'virgo': '/prediction/virgo/tomorrow/',  # Дева
            'libra': '/prediction/libra/tomorrow/',  # Весы
            'scorpio': '/prediction/scorpio/tomorrow/',  # Скорпион
            'sagittarius': '/prediction/sagittarius/tomorrow/',  # Стрелец
            'capricorn': '/prediction/capricorn/tomorrow/',  # Козерог
            'aquarius': '/prediction/aquarius/tomorrow/',  # Водолеи
            'pisces': '/prediction/pisces/tomorrow/'  # Рыбы
        }

        self.text_locator = 'div', {'class': 'article__text'}


class WomenHoroscopes(HoroscopesPage):
    def __init__(self):
        super().__init__('https://goroskop365.ru/')
        self.signs_map = {
            'arises': '/zavtra/aries/',  # Овен
            'taurus': '/zavtra/taurus/',  # Телец
            'gemini': '/zavtra/gemini/',  # Близнецы
            'cancer': '/zavtra/cancer/',  # Рак
            'leo': '/zavtra/leo/',  # Лев
            'virgo': '/zavtra/virgo/',  # Дева
            'libra': '/zavtra/libra/',  # Весы
            'scorpio': '/zavtra/scorpio/',  # Скорпион
            'sagittarius': '/zavtra/sagittarius/',  # Стрелец
            'capricorn': '/zavtra/capricorn/',  # Козерог
            'aquarius': '/zavtra/aquarius/',  # Водолеи
            'pisces': '/zavtra/pisces/'  # Рыбы
        }

        self.text_locator = '.content_wrapper.horoborder > p'
