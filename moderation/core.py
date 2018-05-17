import re

from alphabet_detector import AlphabetDetector
import logging
from vk_api import ApiError

from posting.models import Group
from moderation.models import ModerationRule
from posting.poster import create_vk_api_using_login_password
from settings.models import Setting

log = logging.getLogger('moderation.core')

VK_API_VERSION = Setting.get_value(key='VK_API_VERSION')


def delete_comment(api, owner_id, comment_id):
    try:
        api.wall.deleteComment(owner_id='-{}'.format(owner_id),
                               comment_id=comment_id,
                               api_version=VK_API_VERSION)
    except ApiError as error_msg:
        log.info('Group {} got api error in deleteComment method: {}'.format(owner_id, error_msg))


def is_group(api, commentator_id):
    response = api.groups.getById(group_id=commentator_id,
                                  api_version=VK_API_VERSION)
    error_code = response.get('error_code')
    if error_code == 100:
        return False
    return True


def handle_comment_event(event_object, group_id):
    log.info('start handling comment {} in {}'.format(event_object['id'], group_id))

    group = Group.objects.filter(group_id=group_id)

    moderation_rule = ModerationRule.objects.first()
    if event_object['from_id'] in moderation_rule.id_white_list.split():
        log.info('from_id {} in white list, cancel moderation'.format(event_object['from_id']))
        return False

    api = create_vk_api_using_login_password(group.user.login, group.user.password, group.user.app_id)
    if not api:
        return None

    words_stop_list = set(moderation_rule.words_stop_list.split())
    words_in_text = re.sub("[^\w]", " ", event_object['text']).split()

    if any(word in words_stop_list for word in words_in_text):
        delete_comment(api, group_id, event_object['id'])
        log.info('delete comment {} in {} : stop words in text'.format(event_object['id'], group_id))
        return True

    for word in words_in_text:
        ad = AlphabetDetector()
        if len(ad.detect_alphabet(word)) > 1:
            delete_comment(api, group_id, event_object['id'])
            log.info('delete comment {} in {} : scam words in text'.format(event_object['id'], group_id))
            return True

    if event_object.get('attachments'):
        for attachment in event_object['attachments']:
            if attachment['type'] == 'video':
                delete_comment(api, group_id, event_object['id'])
                log.info('delete comment {} in {} : video in attachments'.format(event_object['id'], group_id))
                return True

    if is_group(api, event_object['id']):
        delete_comment(api, group_id, event_object['id'])
        log.info('delete comment {} in {} : comment from group/community'.format(event_object['id'], group_id))
        return True

    log.info('comment {} in {} was moderated, everything ok'.format(event_object['id'], group_id))