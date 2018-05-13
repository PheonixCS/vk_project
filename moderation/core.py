import re

from posting.models import Group
from moderation.models import ModerationRule
from posting.poster import create_vk_api_using_login_password


def delete_comment(api, owner_id, comment_id):
    api.wall.deleteComment(owner_id='-{}'.format(owner_id),
                           comment_id=comment_id)


def handle_comment_event(event_object, group_id):
    group = Group.objects.filter(group_id=group_id)

    moderation_rule = ModerationRule.objects.first()
    if event_object['from_id'] in moderation_rule.id_white_list:
        return False

    api = create_vk_api_using_login_password(group.user.login, group.user.password, group.user.app_id)
    if not api:
        return None

    # Проверка на наличие ссылок в сообщении
    if re.findall('https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', event_object['text']):
        delete_comment(api, group_id, event_object['id'])
        return True

    # Проверка на наличие стоп-слов в тексте (учитывая замену русских букв на англ)
    # https://github.com/EliFinkelshteyn/alphabet-detector

    # Проверка на наличие attachment видео
    if event_object['attachments']:
        for attachment in event_object['attachments']:
            if attachment['type'] == 'video':
                delete_comment(api, group_id, event_object['id'])
                return True

    # Проверка на комментарий от (from_id) сообщества
