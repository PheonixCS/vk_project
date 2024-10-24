import csv
import json
import os
from cryptography.fernet import Fernet
import time
import re
import random
from texts import dates, symbols, coffee, road
import requests

# Путь к вашему CSV файлу
file_path = 'file.csv'
token = 'gAAAAABm4fMAs0X6vHRHfJPvjRdTFQ3nWueAQwICg1qwdojXdT5AqWbNOCj7plEYSQeq6lLWCY1vWXW-p4c21AqeqBjDYXihz067lJ6kPwI3XWzqz2get_3GluS0JGhvXND-dnap5WAe8GIr_ABCjegWHRvbA-wdBxB9FBbT18Vek7dO_WTLHErdyVNwOxNLmHL6eu-HxGVmcvWdJfflLd0rjqHtkds8cA3Cb35npx7shFobzQbtozJdHR04SfLV_3mywmSFbrWTnv6Z3JcduYtTay2ClV6XOWJ5kE5IBvZtGcO8VBx93-InOOrbqbUaVQJUMTSx4fX-205CGskxXqeE51Xj9k-pK2YfbyVrnSBgeEp20jQOa73ilE0PrscMJBs1Qwt2CSUIwtPHZcg3zpR2eCgQ0odyPQ_wZd6jLnBBlcxUyt04c-A='
# Инициализация списка для хранения данных
data_list = []
crypt = Fernet(key=("18dm6seTSz0b7Eiyonj5acl1Tt_MoxWoTI-K0cwnaq4=").encode())
print(crypt.decrypt(token).decode())

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


# проверка знака зодика по дате
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


# проверка месяца в сообщение
def check_month(month):
    month_nums = {
        'январ': 1,
        'феврал': 2,
        'март': 3,
        'апрел': 4,
        'ма': 5,
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


def get_random_text(file):
    if file == 'путь':
        choice = random.choice(road).strip()
    elif file == 'дата':
        choice = random.choice(dates).strip()
    elif file == 'кофе':
        choice = random.choice(coffee).strip()
    elif file == 'символы':
        choice = random.choice(symbols).strip()

    return choice


def text_answer(input_date):
    text = input_date['object']['text'].lower()
    try:
        text_date = '' + text
        if '[' in text_date and ']' in text_date:
            text_date = text_date.split(',')[1]
        month, eng_month = check_month(re.findall(r'[а-я]+', text_date)[0]), \
        check_month(re.findall(r'[а-я]+', text_date)[0])[1]
        day = (re.findall(r'\d+', text_date))[0]
        if month:
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
                tg_link = f'{get_link_by_mark(zodiac)}#{str(day)}{str(eng_month)}'
                message = get_random_text('дата')
                if input_date['object'].get('reply_to_comment'):
                    return 'Подробный гороскоп для вас: {}'.format(tg_link), zodiac_groups[zodiac.lower()]
                return '{}  Подробный гороскоп для вас: {}'.format(message, tg_link), zodiac_groups[zodiac.lower()]
    #                return None, None
    except Exception as e:
        if any(word in text for word in
               ['овен', 'телец', 'близнец', 'рак', 'лев', 'дев', 'весы', 'скорпион', 'стрел', 'козерог', 'водоле',
                'рыб', 'овны', 'тельцы', 'львы']):
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
                'тельцы': (54365479, 't.me/+E1FtzHxQcgBiMTQy#strelec'),
            }
            for i in ['овен', 'телец', 'близнец', 'рак', 'лев', 'дев', 'весы', 'скорпион', 'стрел', 'козерог', 'водоле',
                      'рыб', 'овны', 'тельцы', 'львы']:
                if i in text:
                    zodiacs = zodiac_groups[i]
                    break
            return f'Подробный гороскоп для вас: {zodiacs[1]}', str(zodiacs[0])
        #            return None, None
        elif (len(text) == 2) and (text.isalpha()):
            return get_random_text('символы'), None
        #            return None, None
        elif text in ['кофе']:
            return get_random_text('кофе'), None
        #            return None, None
        elif text in ['путь']:
            return get_random_text('путь'), None
        #            return None, None
        return None, None


# Открытие CSV файла и чтение содержимого
with open(file_path, mode='r', encoding='utf-8') as file:
    csv_reader = csv.reader(file)

    # Пропускаем заголовок, если он есть
    header = next(csv_reader)

    # Читаем строки из CSV и добавляем их в список
    for row in csv_reader:
        comment = json.loads(row[2])
        message, from_group = text_answer(comment)
        if message:
            data = {
                'owner_id': f"-{comment['group_id']}",
                'comment_id': comment['object']['id'],
                'post_id': comment['object']['post_id'],
                'message': message,
                'token': crypt.decrypt(token).decode(),
                'from_group': from_group}
            if not from_group:
                from_group = data['owner_id'][1:]
            headers = {
                'Authorization': f'Bearer {data["token"]}'
            }

            response = requests.post(
                'https://api.vk.com/method/wall.createComment',
                headers=headers,
                params={
                    'owner_id': data['owner_id'],
                    'post_id': data['post_id'],
                    'from_group': from_group,
                    'reply_to_comment': data['comment_id'],
                    'message': message,
                    'v': '5.195'
                }
            )

            print(response.json())
            time.sleep(1)