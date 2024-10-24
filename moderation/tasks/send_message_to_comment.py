import logging
import time
import random
from moderation.models import Filter
import requests
from moderation.models import UserDataSubscribe
import ast

log = logging.getLogger('moderation.tasks')



def check_subscribe(token: str, group_id: int, user_ids: list):
    '''Проверка на подписку, проверяем сразу пачку людей, чтобы обойти ограничение на запросы в сутки'''
    headers = {
            'Authorization': f'Bearer {token}'
        }
        
    response = requests.post(
            'https://api.vk.com/method/groups.isMember', 
            headers=headers, 
            params={
                'group_id': group_id,
                'user_ids': ','.join(map(str, user_ids)),
                'v':'5.199'
            }
        )
    log.info("user_ids: {}".format(user_ids))
    log.info("Member resp: {}".format(response.json()))
    return response.json()


def get_user_firstname(user_id: int, token: str) -> str:
    '''Функция получение имени для отправки уведомления о подписке'''
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
    return f"[id{user_id}|{response['response'][0]['first_name']}], "

def like_comment(token, user_id, comment_id, group_id):
    headers = {
            'Authorization': f'Bearer {token}'
        }
        
    response = requests.post(
            'https://api.vk.com/method/likes.add', 
            headers=headers, 
            params={
                'type': 'comment',
                'item_id': group_id,
                'owner_id': user_id,
                'from_group': 1,
                'v':'5.195'
            }
        )


def safe_eval(path, variables=None):
    with open(f'media/{path}', 'r', encoding='utf-8') as answers_file:
        expr = answers_file.read()
        if variables is None:
            variables = {}
        parsed_expr = ast.parse(expr, mode='eval')
        code = compile(parsed_expr, '<string>', 'eval')
        return eval(code, {"__builtins__": {}}, variables)


def comment_invite(data):
    '''Функция отправки уведомления о подписке'''
    # Спим 1 секунду, чтобы не отпрвить слишком много запросов в сек
    # Пробуем отправить уведомление ТОЛЬКО 1 раз, так как обычные ответы важнее
    time.sleep(2)
    zodiac_groups = {
        54365470: ('ОВЕН','goroskop_oven1'),
        54365479: ('ТЕЛЕЦ','goroskop_telec2'),
        54365482: ('БЛИЗНЕЦЫ', 'goroskop_bliznecy3'),
        54365511: ('РАК', 'goroskop_rak4'),
        54365524: ('ЛЕВ', 'goroskop_lev5'),
        54365538: ('ДЕВА', 'goroskop_deva6'),
        54365550: ('ВЕСЫ', 'goroskop_vesy7'),
        54365555: ('СКОРПИОН', 'goroskop_skorpion8'),
        54365563: ('СТРЕЛЕЦ', 'goroskop_strelec9'),
        54365565: ('КОЗЕРОГ', 'goroskop_kozerog10'),
        54365575: ('ВОДОЛЕЙ', 'goroskop_vodoley11'),
        54365581: ('РЫБЫ', 'goroskop_ryby12'),
    }
    headers = {
        'Authorization': f'Bearer {data["token"]}'
    }
    firstname = get_user_firstname(data['params']['user_id'], data['token'])
    # message = f"{firstname}мы заметили, что вы не подписаны на [exp.horoscope|наше сообщество]. Подпишитесь, чтобы не потерять нас 🙏 БЛАГО ДАРЮ!" 
    keywords = Filter.objects.filter(keywords='уведомлениеоподписке').values()
    grouplink = zodiac_groups.get(int(data['params']['from_group']))
    if not grouplink:
        grouplink = ('наше сообщество', 'exp.horoscope')
    variables = {
        'grouplink': grouplink
    }
    answers = safe_eval(keywords[0].get('answers'), variables)
    message = f'{firstname}{answers[0]}'      
    if grouplink[1] != 'exp.horoscope':
        message = f'{firstname}{answers[1]}' 
    response = requests.post(
        'https://api.vk.com/method/wall.createComment', 
        headers=headers, 
        params={
            'owner_id': data['params']['owner_id'],
            'post_id': data['params']['post_id'],
            'from_group': data['params']['from_group'],
            'reply_to_comment': data['params']['reply_to_comment'],
            'message': message,
            'v':'5.195'
        }
    )
    log.info('celery 30 min response {}'.format(response.json()))


def callback(data, delay):
    try:
        # Отправка основного комента (здесь только ответы на ключевики)
        log.info("In callback function thread")
        
        time.sleep(delay)
        log.info("After waiting")
        
        if not data['params']['from_group']:
            data['params']['from_group'] = data['params']['owner_id'][1:]
        headers = {
            'Authorization': f'Bearer {data["token"]}'
        }
        response = requests.post(
            'https://api.vk.ru/method/wall.createComment', 
            headers=headers, 
            params={
                'owner_id': data['params']['owner_id'],
                'post_id': data['params']['post_id'],
                'from_group': data['params']['from_group'],
                'reply_to_comment': data['params']['reply_to_comment'],
                'message': data['params']['message'],
                'v':'5.195'
            }
        )
        try:
            resp = response.json()
        except:
            resp = response.text
        # Если вылетает одна из этих ошибок то пробуем отправить, пока таска селери автоматом не потушит поток
        # 9 ошибку лучше не трогать, если она вылетает значит что то делаете не так 
        # Рандомная задержка, чтобы нагрузка хоть как то раскидывалась, желательно переписать
        if resp.get('error'):
            if resp['error'].get('error_code') == 6:
                log.info("Retry")
                callback(data=data, delay=random.randint(1, 10))
            # elif resp['error'].get('error_code') == 9:
            #     log.info("Retry")
            #     callback(data=data, delay=random.randint(5, 10))
            # elif resp['error'].get('error_code') == 14:
            #     log.info("Capcha")
            #     callback(data=data, delay=random.randint(1, 15))
            elif resp['error'].get('error_code') == 29:
                log.info("Rate limit")
                callback(data=data, delay=random.randint(1, 10))
        else:
            # В случае успешной отправки ответа на комент, добаляем пользователя которому ответили в базу на проверку подписки
            #UserDataSubscribe.add_user(data['params']['user_id'], data['params']['from_group'], data['params']['reply_to_comment'], data['params']['post_id'], data['params']['owner_id'])
            # ВК позволяет отправить около 2000 запросов на проверку подписки в день, в доке есть инфа про отправку сразу пачки людей
            # Так обходим лимит и получаем 600000 проверенных коментов на подписку в день, сейчас хватает с запасом
            if UserDataSubscribe.objects.count() >= 30:
                # Когда накопили определенное кол-во пользователей проверяем у них разом подписки чтобы не упираться в лимит в сутки
                # Сейчас реализовано через все озможные костыли, если есть желание можно переписать
                users_messages = UserDataSubscribe.objects.all()
                users_ids = [(int(message.user_id), message.group_id) for message in users_messages]
                user_data = [(int(message.user_id), message.group_id, message.comment_id, message.post_id, message.owner_id) for message in users_messages]

                # Когда получили всех пользователь и засейвили в переменные, полностью чистим модель чтобы другие потоки не успели догнать 
                UserDataSubscribe.clear_model()


                log.info("{}".format(users_ids))                
                ismember = {}
                # Делим всех пользователь по группе которая им ответила, потому что проверять нужно конкретную группу которая ответила
                for group in [29038248, 54365470, 54365479, 54365482, 54365511, 54365524, 54365538, 54365550, 54365555, 54365563, 54365565, 54365575, 54365581]:
                    result = list(map(lambda x: x[0], filter(lambda x: x[1] == str(group), users_ids)))
                    # Вроде ВК позволяет проверять по id группы, но почему то не работало поэтому чекаем по индентификатору
                    # Если время есть надо проверить по id, мб будет работать
                    indification_groups = {
                        54365470: 'goroskop_oven1',
                        54365479: 'goroskop_telec2',
                        54365482: 'goroskop_bliznecy3',
                        54365511: 'goroskop_rak4',
                        54365524: 'goroskop_lev5',
                        54365538: 'goroskop_deva6',
                        54365550: 'goroskop_vesy7',
                        54365555: 'goroskop_skorpion8',
                        54365563: 'goroskop_strelec9',
                        54365565: 'goroskop_kozerog10',
                        54365575: 'goroskop_vodoley11',
                        54365581: 'goroskop_ryby12',
                        29038248: 'exp.horoscope'
                    }
                    # Сейвим результаты от всех групп в одну переменную
                    if result:
                        ismember[group] = (check_subscribe(data["token"], indification_groups.get(group), result)).get('response')
                # Если пользователь не в группе то отправляем ему уведомление
                if ismember:
                    for group in [29038248, 54365470, 54365479, 54365482, 54365511, 54365524, 54365538, 54365550, 54365555, 54365563, 54365565, 54365575, 54365581]:
                        if ismember.get(group):
                            for user in ismember[group]:
                                if user.get('member') == 0:
                                    users_mess = []
                                    for i in range(len(user_data)):
                                        if user_data[i][0] == int(user.get('user_id')) and int(user_data[i][1]) == group:
                                            users_mess = user_data[i]
                                            user_data.pop(i)
                                            break
                                    if users_mess:
                                        messdata = {
                                            'token': data["token"],
                                            'params': {
                                                'user_id': users_mess[0],
                                                'from_group': users_mess[1],
                                                'reply_to_comment': users_mess[2],
                                                'post_id': users_mess[3],
                                                'owner_id': users_mess[4]
                                            }
                                        }
                                        comment_invite(messdata)
        log.info("Response: {}".format(resp))
    except Exception as e:
        log.error("error: {}".format(e))