import re

from alphabet_detector import AlphabetDetector
from urlextract import URLExtract
import logging
from vk_api import ApiError

from posting.models import Group
from moderation.models import ModerationRule
from posting.poster import create_vk_session_using_login_password
from settings.models import Setting
from django.db.models import Q


log = logging.getLogger('moderation.core')

VK_API_VERSION = Setting.get_value(key='VK_API_VERSION')


def delete_comment(api, owner_id, comment_id):
    try:
        api.wall.deleteComment(owner_id='-{}'.format(owner_id),
                               comment_id=comment_id,
                               api_version=VK_API_VERSION)
    except ApiError as error_msg:
        log.info('Group {} got api error in deleteComment method: {}'.format(owner_id, error_msg))


def is_group(commentator_id):
    if int(commentator_id) < 0:
        return True


def prepare_id_white_list(white_list):
    white_list = re.sub('(id)', '', white_list)
    white_list = re.sub('[^\s\d]+', '-', white_list)
    return white_list.split()


def is_post_ad(api, post_id, group_id):
    try:
        post = api.wall.getById(posts='-{}_{}'.format(group_id, post_id),
                                api_version=VK_API_VERSION)
    except ApiError as error_msg:
        log.info('Group {} post {} got api error in getById method: {}'.format(group_id, post_id, error_msg))
        return None
    return post[0].get('marked_as_ads', False)


def handle_comment_event(event_object, group_id):
    log.info('start handling comment {} in {} by {}'.format(event_object['id'], group_id, event_object['from_id']))

    group = Group.objects.select_related('user').filter(group_id=group_id).first()

    moderation_rule = ModerationRule.objects.first()
    if event_object['from_id'] in list(map(int, prepare_id_white_list(moderation_rule.id_white_list))):
        log.info('from_id {} in white list, cancel moderation'.format(event_object['from_id']))
        return False

    api = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id).get_api()
    if not api:
        log.warning('no api created!')
        return None

    if is_post_ad(api, event_object['post_id'], group_id):
        delete_comment(api, group_id, event_object['id'])
        log.info('delete comment {} in {} : post marked as ad'.format(event_object['id'], group_id))
        return True

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

    if is_group(event_object['from_id']):
        delete_comment(api, group_id, event_object['id'])
        log.info('delete comment {} in {} : comment from group/community'.format(event_object['id'], group_id))
        return True

    extractor = URLExtract()
    if extractor.has_urls(event_object['text']):
        delete_comment(api, group_id, event_object['id'])
        log.info('delete comment {} in {} : contains links'.format(event_object['id'], group_id))
        return True

    log.info('comment {} in {} was moderated, everything ok'.format(event_object['id'], group_id))


def does_group_exist(group_id):
    # TODO may be this is slow
    group = Group.objects.filter(Q(group_id=group_id) | Q(domain_or_id__contains=str(group_id))).first()

    return group


def get_callback_api_key(group_id):
    group = Group.objects.filter(Q(group_id=group_id) | Q(domain_or_id__contains=str(group_id))).first()
    token = group.callback_api_token

    log.debug('got callback token for group {}'.format(group_id))

    return token
