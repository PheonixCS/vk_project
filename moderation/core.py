import re

from alphabet_detector import AlphabetDetector

from posting.models import Group
from moderation.models import ModerationRule
from posting.poster import create_vk_api_using_login_password
from settings.models import Setting

VK_API_VERSION = Setting.get_value(key='VK_API_VERSION')


def delete_comment(api, owner_id, comment_id):
    api.wall.deleteComment(owner_id='-{}'.format(owner_id),
                           comment_id=comment_id,
                           api_version=VK_API_VERSION)


def is_group(api, commentator_id):
    response = api.groups.getById(group_id=commentator_id,
                                  api_version=VK_API_VERSION)
    error_code = response.get('error_code')
    if error_code == 100:
        return False
    return True


def handle_comment_event(event_object, group_id):
    group = Group.objects.filter(group_id=group_id)

    moderation_rule = ModerationRule.objects.first()
    if event_object['from_id'] in moderation_rule.id_white_list.split():
        return False

    api = create_vk_api_using_login_password(group.user.login, group.user.password, group.user.app_id)
    if not api:
        return None

    # Проверка на наличие стоп-слов в тексте (учитывая замену русских букв на англ)
    words_stop_list = set(moderation_rule.words_stop_list.split())
    words_in_text = re.sub("[^\w]", " ", event_object['text']).split()

    if any(word in words_stop_list for word in words_in_text):
        delete_comment(api, group_id, event_object['id'])
        return True

    for word in words_in_text:
        ad = AlphabetDetector()
        if len(ad.detect_alphabet(word)) > 1:
            delete_comment(api, group_id, event_object['id'])
            return True

    # Проверка на наличие прикрепленного видео
    if event_object.get('attachments'):
        for attachment in event_object['attachments']:
            if attachment['type'] == 'video':
                delete_comment(api, group_id, event_object['id'])
                return True

    # Проверка на комментарий от (from_id) сообщества
    if is_group(api, event_object['id']):
        delete_comment(api, group_id, event_object['id'])
        return True
