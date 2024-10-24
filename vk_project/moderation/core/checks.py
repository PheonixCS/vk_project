import logging
import os
import re
import typing
import requests
import random
from alphabet_detector import AlphabetDetector
from urlextract import URLExtract
from .texts import road, dates, symbols, coffee, tarot
from constance import config
from moderation.models import Filter, KeywordMessage
from services.text_utilities import delete_emoji_from_text
import ast
from django.utils import timezone
from datetime import timedelta


log = logging.getLogger('moderation.core.checks')

# TODO need tests
def is_stop_words_in_text(stop_list, text):
    if any(word in stop_list for word in text):
        log.debug('found stop word in text')
        return True


def is_scam_words_in_text(text: list):
    for word in text:
        ad = AlphabetDetector()
        if len(ad.detect_alphabet(word)) > 1:
            log.debug('found scam word in text')
            return True


# TODO need tests
def is_video_in_attachments(attachments):
    for attachment in attachments:
        if attachment['type'] == 'video':
            log.debug('found video in attachments')
            return True


# TODO need tests
def is_link_in_attachments(attachments):
    for attachment in attachments:
        if attachment['type'] == 'link':
            log.debug('found link in attachments')
            return True


# TODO need tests
def is_group(commentator_id):
    if int(commentator_id) < 0:
        log.debug('from_id is group')
        return True


# TODO need tests
def is_links_in_text(text):
    text_without_emoji = delete_emoji_from_text(text)
    extractor = URLExtract()
    if extractor.has_urls(text_without_emoji):
        log.debug('found url in text')
        return True


# TODO need tests
def is_vk_links_in_text(text):
    if re.findall(r'\[club.*?\|.*?\]', text):
        log.debug('found vk link in text')
        return True


# TODO need tests
def is_audio_and_photo_in_attachments(attachments):
    if is_audio_in_attachments(attachments) and is_photo_in_attachments(attachments):
        return True


# TODO need tests
def is_audio_in_attachments(attachments):
    if [attachment for attachment in attachments if attachment['type'] == 'audio']:
        log.debug('found audio in attachments')
        return True


# TODO need tests
def is_photo_in_attachments(attachments):
    if [attachment for attachment in attachments if attachment['type'] == 'photo']:
        log.debug('found photo in attachments')
        return True


# Все ссылки на тг по знакам 
def get_link_by_mark(mark: str):
    all_marks = {
        "ОВЕН": "t.me/+TlSW7jOu9zdhNWE6",
        "ТЕЛЕЦ": "t.me/+Tp_nePEyByplOTAy",
        "БЛИЗНЕЦЫ": "t.me/+ysXJaFQGuw0wYzZi",
        "РАК": "t.me/+b5yXgO35m7BhYmQy",
        "ЛЕВ": "t.me/+W_FFpw0akStkOGE6",
        "ДЕВА": "t.me/+bOQGMybY-sA1MTgy",
        "ВЕСЫ": "t.me/+-R6I8_qRgcQ1NTdi",
        "СКОРПИОН": "t.me/+BCWF4OJ_t1xiNTRi",
        "СТРЕЛЕЦ": "t.me/+E1FtzHxQcgBiMTQy",
        "КОЗЕРОГ": "t.me/+t3oixSNuEw0zNmIy",
        "ВОДОЛЕЙ": "t.me/+tGsYjj5oDKBjYjgy",
        "РЫБЫ": "t.me/+p7wKPT41wxdkMThi"
    }
    return all_marks[mark]


# Проверка знака зодика по дате
def zodiac_sign(day, month):
    if (month == 1 and day >= 20) or (month == 2 and day <= 18):
        return "ВОДОЛЕЙ"
    if (month == 2 and 29 >= day >= 19) or (month == 3 and day <= 20):
        return "РЫБЫ"
    if (month == 3 and day >= 21) or (month == 4 and day <= 19):
        return "ОВЕН"
    if (month == 4 and day >= 20) or (month == 5 and day <= 20):
        return "ТЕЛЕЦ"
    if (month == 5 and day >= 21) or (month == 6 and day <= 20):
        return "БЛИЗНЕЦЫ"
    if (month == 6 and day >= 21) or (month == 7 and day <= 22):
        return "РАК"
    if (month == 7 and day >= 23) or (month == 8 and day <= 22):
        return "ЛЕВ"
    if (month == 8 and day >= 23) or (month == 9 and day <= 22):
        return "ДЕВА"
    if (month == 9 and day >= 23) or (month == 10 and day <= 22):
        return "ВЕСЫ"
    if (month == 10 and day >= 23) or (month == 11 and day <= 21):
        return "СКОРПИОН"
    if (month == 11 and day >= 22) or (month == 12 and day <= 21):
        return "СТРЕЛЕЦ"
    if (month == 12 and day >= 22) or (month == 1 and day <= 19):
        return "КОЗЕРОГ"
    return None


# Проверка месяца в сообщение
def check_month(month):
    month_nums = {
        'январ': 1,
        'феврал': 2,
        'март': 3,
        'апрел': 4,
        'май': 5,
        'мая': 5,
        'июн': 6,
        'июл': 7,
        'август': 8,
        'сентябр': 9,
        'октябр': 10,
        'ноябр': 11,
        'декабр': 12
    }
    month_mapping = {
        1: 'january',
        2: 'february',
        3: 'march',
        4: 'april',
        5: 'may',
        6: 'june',
        7: 'july',
        8: 'august',
        9: 'september',
        10: 'october',
        11: 'november',
        12: 'december'
    }
    for key in month_nums.keys():
        if key in month:
            return month_nums[key], month_mapping[month_nums[key]]
    return None


# Устарело
def get_random_text(file):
    if file == 'путь':
        choice = random.choice(road).strip()
    elif file == 'дата':
        choice = random.choice(dates).strip()
    elif file == 'кофе':
        choice = random.choice(coffee).strip()
    elif file == 'символы':
        choice = random.choice(symbols).strip()    
    elif file == 'таро':
        choice = random.choice(tarot).strip()    
    
    return choice

# Получение случайного ответа, из файла по ключевику
def get_random_str_from_txt(file_path: str) -> str:
    # with open(file, 'r', encoding='utf-8') as file:
    #     lines = file.readlines()  # Читаем все строки из файла
    #     return random.choice(lines).strip()  # Возвращаем случайную строку без лишних пробелов    
    with open(f'media/{file_path}', 'r', encoding='utf-8') as file:
        content = file.read()
        sentences = ast.literal_eval(content)  # Преобразуем строку в список
        return random.choice(sentences)  # Возвращаем случайное предложение


# Удаление всех смайликов из текста
def remove_emojis(text: str) -> str:
    # Регулярное выражение для поиска эмодзи
    emoji_pattern = re.compile(
        "[\U0001F100-\U0001F9FF"  # Общие эмодзи
        "\U0001F600-\U0001F64F"  # Лица
        "\U0001F300-\U0001F5FF"  # Символы и пиктограммы
        "\U0001F680-\U0001F6FF"  # Транспорт
        "\U0001F700-\U0001F7FF"  # Математические символы
        "\U0001F800-\U0001F8FF"  # Стрелки и дополнительные символы
        "\U0001F900-\U0001F9FF"  # Инновации
        "\u2600-\u26FF"  # Символы
        "\u2700-\u27BF"  # Символы
        "\u2B50"  # Звезда
        "\uE005-\uE007"  # Другие эмодзи
        "]+", flags=re.UNICODE)

    return emoji_pattern.sub('', text)


# Функция для получения имени пользователя
def get_user_firstname(user_id: str, token: str) -> str:
    headers = {
            'Authorization': f'Bearer {token}'
        }
        
    response = requests.post(
            'https://api.vk.com/method/users.get', 
            headers=headers, 
            params={
                'user_ids': user_id,
                'v':'5.195'}
        ).json()
    log.info("Info about user: {}".format(response['response'][0]))
    return response['response'][0]['first_name']


# Проверка, было ли последнее сообщение с ключевиком отправлено раньше 8 часов назад
def check_lasttime(user_id: str, keyword: str) -> bool:
    last_message = KeywordMessage.last_message_with_keyword(user_id, keyword)
    if last_message:
        log.info('time {}'.format(last_message.timestamp))
        if last_message.timestamp >= (timezone.now() - timedelta(hours=8)):
            return True
    return False


# Обновление времени последнего запроса от пользователя
def update_lasttime(user_id: str, keyword: str):
    KeywordMessage.add_or_update_message(user_id, keyword)


# Все лишнее то что просил Павел, тут удаляем
def clear_specsymbols(text: str) -> str:
    text = text.replace('"','')
    text = text.replace('!','')
    text = text.replace('?','')    
    text = text.replace(')','')    
    text = text.replace('(','')    
    text = text.replace('да будет так.','')
    text = text.replace('да будет так,','')
    text = text.replace('да будет так','')
    text = text.replace('благодарю.','')
    text = text.replace('благодарю,','')
    text = text.replace('благодарю','')
    text = text.replace('во благо.','')
    text = text.replace('во благо,','')
    text = text.replace('во благо','')
    text = text.replace('принимаю.','')
    text = text.replace('принимаю,','')
    text = text.replace('принимаю','')
    text = text.replace('совпало.','')
    text = text.replace('совпало,','')
    text = text.replace('совпало','')
    text = text.replace('спасибо.','')
    text = text.replace('спасибо,','')
    text = text.replace('спасибо','')
    text = text.replace('гороскоп & таро,','')
    text = text.replace('гороскоп & таро','')
    text = text.replace('гороскоп,','')
    text = text.replace('гороскоп','')
    
    text = text.replace("'",'')
    return text


# Основой функционал поиска ключевиков в коменте
def text_answer(input_date, token):
    log.info("{}".format(input_date))
    log.info("TEST 222222222222222222222")
    text = input_date['object']['text'].lower()
    text = clear_specsymbols(text)
    text = remove_emojis(text)
    log.info("text: {}".format(text))
    # Получение имени человека, если респонс с ошибкой то отвечаем без тега
    try:
        firstname = f"[id{input_date['object']['from_id']}|{get_user_firstname(input_date['object']['from_id'], token)}], "
    except:
        firstname = ''
    # Удаление тега из комента "[id88888|text]"
    if '[' in text and ']' in text:
        textlist = text.split(',')
        textlist.pop(0)
        text = ''.join(textlist)
    text.strip()
    keywords = Filter.objects.values()
    log.info('filter {}Х'.format(keywords))
    log.info('text {}'.format(text))
    # Проход по всем ключевым словам которые есть в админке
    for i in keywords:
        if i.get('keywords') == 'даты':
            # Даты сейчас работают на божьей помощи, надо переписать
            try:
                text_date = '' + text.strip()
                day, month = None, None
                if '[' in text_date and ']' in text_date:
                    text_date = text_date.split(',')[1]
                text1_date = text_date + ''
                try:
                    # Общий try для поиска даты форматов "xx.xx.xxxx" "xx.xx" с любыми разделителями вместо .
                    if len(text1_date) >= 4:
                        try:
                            day, month = int(text1_date[:2]), int(text1_date[2:4])
                            if month <= 0 or text1_date[2] == ' ':
                                day, month = None, None 
                                day, month = int(text1_date.split('-')[0]), int(text1_date.split('-')[1])
                        except:
                            for year in range(1950, 2031):
                                for symbol in [',', '.', ';', '!', '/']:
                                    text1_date = text1_date.replace(f'{symbol}{str(year)}г.', '')
                                    text1_date = text1_date.replace(f'{symbol}{str(year)}г', '')
                                    text1_date = text1_date.replace(f'{symbol}{str(year)}', '')
                                    text1_date = text1_date.replace(f'{str(year)}г.', '')
                                    text1_date = text1_date.replace(f'{str(year)}г', '')
                                    text1_date = text1_date.replace(str(year), '')
                            text1_date = text1_date.strip()
                            try:
                                day, month = int(text1_date.split('.')[0]), int(text1_date.split('.')[1])
                            except:
                                try:
                                    day, month = int(text1_date.split(' ')[0]), int(text1_date.split(' ')[1])
                                except:
                                    try:
                                        day, month = int(text1_date.split(';')[0]), int(text1_date.split(';')[1])
                                    except:
                                        try:
                                            day, month = int(text1_date.split('-')[0]), int(text1_date.split('-')[1])
                                        except:
                                            try:
                                                day, month = int(text1_date.split(',')[0]), int(text1_date.split(',')[1])
                                            except:
                                                try:
                                                    day, month = int(text1_date.split(':')[0]), int(text1_date.split(':')[1])
                                                except:
                                                    try:
                                                        day, month = int(text1_date[:2]), int(text1_date[2:4])
                                                    except:
                                                        day, month = None, None
                    if 1 <= month <= 12:
                        eng_month = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'][month - 1]
                        if zodiac := zodiac_sign(int(day), month):
                            zodiac_groups = {
                                'овен': 54365470,
                                'телец': 54365479,
                                'близнецы': 54365482,
                                'рак': 54365511,
                                'лев': 54365524,
                                'дева': 54365538,
                                'весы': 54365550,
                                'скорпион': 54365555,
                                'стрелец': 54365563,
                                'козерог': 54365565,
                                'водолей': 54365575,
                                'рыбы': 54365581,
                            }
                            tg_link = f"{get_link_by_mark(zodiac)}#{str(day)}{eng_month}"
                            message = get_random_str_from_txt(i.get('answers'))
                            if check_lasttime(input_date['object']['from_id'], 'даты'):
                                return '{} cегодня вы уже запрашивали персональный гороскоп. К астрологии не стоит прибегать так часто, потому что это скажется на точности гороскопа! Вы можете повторить попытку через 8 часов⏳'.format(firstname), 29038248
                            update_lasttime(input_date['object']['from_id'], 'даты')
                            return '{}{}  Подробный гороскоп: {} \n\nНапишите в ответ слово ТАРО и получите личное предсказание от таролога 🎴\n\nПогадать в личных сообщениях 👉 vk.com/im?sel=-29038248'.format(firstname, message, tg_link), zodiac_groups[zodiac.lower()]
                except Exception as e:
                    log.info('error{}'.format(e))
                # Если не находим дату числового формата пробуем найти формата "xx месяц"
                for year in range(1950, 2031):
                    for symbol in [',', '.', ';', '!', '/']:
                        text_date = text_date.replace(f'{symbol}{str(year)}г.', '')
                        text_date = text_date.replace(f'{symbol}{str(year)}г', '')
                        text_date = text_date.replace(f'{symbol}{str(year)}', '')
                        text_date = text_date.replace(f'{str(year)}г.', '')
                        text_date = text_date.replace(f'{str(year)}г', '')
                        text_date = text_date.replace(str(year), '')
                text_date = text_date.strip()
                month, eng_month = check_month(re.findall(r'[а-я]+', text_date)[0]), check_month(re.findall(r'[а-я]+', text_date)[0])[1]
                day = (re.findall(r'\d+', text_date))[0]
                if month:
                    log.info("month {}".format(month))
                    if zodiac := zodiac_sign(int(day), month[0]):
                        zodiac_groups = {
                        'овен': 54365470,
                        'телец': 54365479,
                        'близнецы': 54365482,
                        'рак': 54365511,
                        'лев': 54365524,
                        'дева': 54365538,
                        'весы': 54365550,
                        'скорпион': 54365555,
                        'стрелец': 54365563,
                        'козерог': 54365565,
                        'водолей': 54365575,
                        'рыбы': 54365581,
                        }
                        log.info("{}".format(zodiac))
                        tg_link = f"{get_link_by_mark(zodiac)}#{str(day)}{str(eng_month)}"
                        log.info("{}".format(tg_link))
                        message = get_random_str_from_txt(i.get('answers'))
                        if check_lasttime(input_date['object']['from_id'], 'даты'):
                            return '{} cегодня вы уже запрашивали персональный гороскоп. К астрологии не стоит прибегать так часто, потому что это скажется на точности гороскопа! Вы можете повторить попытку через 8 часов⏳'.format(firstname), 29038248
                        update_lasttime(input_date['object']['from_id'], 'даты')
                        return '{}{}  Подробный гороскоп: {} \n\nНапишите в ответ слово ТАРО и получите личное предсказание от таролога 🎴\n\nПогадать в личных сообщениях 👉 vk.com/im?sel=-29038248'.format(firstname, message, tg_link), zodiac_groups[zodiac.lower()]
            except:
                pass
        # Все отдельные ответы, нужны для ответов на кастомные ключевики которые через админку не добавить
        # Ключевик состоящий из двух букв 
        elif i.get('keywords') == 'двасимвола':
            if (len(text) == 2) and (text.isalpha()):
                log.info("2 symbols")
                if check_lasttime(input_date['object']['from_id'], 'двасимвола'):
                    return '{} cегодня вы уже запрашивали персональный гороскоп. К астрологии не стоит прибегать так часто, потому что это скажется на точности гороскопа! Вы можете повторить попытку через 8 часов⏳'.format(firstname, i['onlyword']), 29038248
                update_lasttime(input_date['object']['from_id'], 'двасимвола')
                return firstname + get_random_str_from_txt(i.get('answers')), 29038248
        # Знаки зодиака в любом склонение
        elif i.get('keywords') == 'знакизодиака':
            if any(word in text for word in ['овен', 'телец', 'близнец', 'рак', 'лев', 'дев', 'весы', 'скорпион', 'стрел', 'козерог', 'водоле', 'рыб', 'овны', 'тельцы', 'львы']):
                zodiac_groups = {
                    'овен': (54365470, 't.me/+TlSW7jOu9zdhNWE6#oven'),
                    'овны': (54365470, 't.me/+TlSW7jOu9zdhNWE6#oven'),
                    'телец': (54365479, 't.me/+Tp_nePEyByplOTAy#telec'),
                    'близнец': (54365482, 't.me/+ysXJaFQGuw0wYzZi#bliznecy'),
                    'рак': (54365511, 't.me/+b5yXgO35m7BhYmQy#rak'),
                    'лев': (54365524, 't.me/+W_FFpw0akStkOGE6#lev'),
                    'дев': (54365538, 't.me/+bOQGMybY-sA1MTgy#deva'),
                    'весы': (54365550, 't.me/+-R6I8_qRgcQ1NTdi#vesy'),
                    'скорпион': (54365555, 't.me/+BCWF4OJ_t1xiNTRi#skorpion'),
                    'стрел': (54365563, 't.me/+E1FtzHxQcgBiMTQy#strelec'),
                    'козерог': (54365565, 't.me/+t3oixSNuEw0zNmIy#kozerog'),
                    'водоле': (54365575, 't.me/+tGsYjj5oDKBjYjgy#vodolei'),
                    'рыб': (54365581, 't.me/+p7wKPT41wxdkMThi#ryby'),
                    'львы': (54365524, 't.me/+W_FFpw0akStkOGE6#lev'),
                    'тельцы': (54365479, 't.me/+Tp_nePEyByplOTAy#telec'),
                }
                for j in ['овен', 'телец', 'близнец', 'рак', 'лев', 'дев', 'весы', 'скорпион', 'стрел', 'козерог', 'водоле', 'рыб', 'овны', 'тельцы', 'львы']:
                    if j in text:
                        zodiacs = zodiac_groups[j]
                        break
                log.info("marks zodiac")
                message = get_random_str_from_txt(i.get('answers'))
                return f'{firstname}{message} {zodiacs[1]}\n\nНапиши дату рождения в комментариях и получи личный гороскоп от астролога ✨', str(zodiacs[0])
        # Таро вынесено отдельно, чтобы сделать отдельный ответ о превышение запросов за 8 часов
        elif i.get('keywords') == 'таро':
            text_clear = text + ''
            text_clear = text_clear.replace('.','')
            text_clear = text_clear.replace(',',' ')
            if i['onlyword']:
                if any(word in text_clear for word in i.get('keywords').split(';')):
                    if check_lasttime(input_date['object']['from_id'], i.get('keywords').split(';')[0]):
                        # update_lasttime(input_date['object']['from_id'], i.get('keywords').split(';')[0])
                        return '{} сегодня вы уже запрашивали персональный расклад. К картам таро не стоит прибегать так часто, потому что это скажется на точности расклада! Вы можете повторить попытку через 8 часов⏳'.format(firstname, i.get('keywords').split(';')[0]), 29038248
                    update_lasttime(input_date['object']['from_id'], i.get('keywords').split(';')[0])
                    return firstname + get_random_str_from_txt(i.get('answers')), 29038248
            else:
                text_clear = text_clear.strip()
                if text_clear in i.get('keywords').split(';'):
                    if check_lasttime(input_date['object']['from_id'], i.get('keywords').split(';')[0]):
                        # update_lasttime(input_date['object']['from_id'], i.get('keywords').split(';')[0])
                        return '{} сегодня вы уже запрашивали персональный расклад. К картам таро не стоит прибегать так часто, потому что это скажется на точности расклада! Вы можете повторить попытку через 8 часов⏳'.format(firstname, i.get('keywords').split(';')[0]), 29038248
                    update_lasttime(input_date['object']['from_id'], i.get('keywords').split(';')[0])
                    return firstname + get_random_str_from_txt(i.get('answers')), 29038248
        
        # Все обычные ключевики в админке
        else:
            text_clear = text + ''
            text_clear = text_clear.replace('.','')
            text_clear = text_clear.replace(',',' ')
            # Параметр отвечающий за поиск ключевого слова в предложении
            if i['onlyword']:
                if any(word in text_clear for word in i.get('keywords').split(';')):
                    if check_lasttime(input_date['object']['from_id'], i.get('keywords').split(';')[0]):
                        # update_lasttime(input_date['object']['from_id'], i.get('keywords').split(';')[0])
                        againword = next((word for word in i.get('keywords').split(';') if word in text_clear), None)
                        return '{} сегодня вы уже обращались ко вселенной с запросом {}. Ее не стоит беспокоить так часто одинаковыми запросами. Вы можете повторить попытку через 8 часов ⌛️'.format(firstname, againword.upper()), 29038248
                    update_lasttime(input_date['object']['from_id'], i.get('keywords').split(';')[0])
                    return firstname + get_random_str_from_txt(i.get('answers')), 29038248
            else:
                log.info('keyword {}'.format(i['keywords'].split(';')))
                text_clear = text_clear.strip()
                if text_clear in i.get('keywords').split(';'):
                    if check_lasttime(input_date['object']['from_id'], i.get('keywords').split(';')[0]):
                        # update_lasttime(input_date['object']['from_id'], i.get('keywords').split(';')[0])
                        againword = next((word for word in i.get('keywords').split(';') if word in text_clear), None)
                        return '{} сегодня вы уже обращались ко вселенной с запросом {}. Ее не стоит беспокоить так часто одинаковыми запросами. Вы можете повторить попытку через 8 часов ⌛️'.format(firstname, againword.upper()), 29038248
                    update_lasttime(input_date['object']['from_id'], i.get('keywords').split(';')[0])
                    return firstname + get_random_str_from_txt(i.get('answers')), 29038248
    log.info("nothing")
    return None, None
        