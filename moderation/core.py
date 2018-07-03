import re
import logging

from vk_api import ApiError

from posting.models import Group
from moderation.models import ModerationRule
from posting.poster import create_vk_session_using_login_password
from settings.models import Setting
from django.db.models import Q
import moderation.checks as checks

log = logging.getLogger('moderation.core')

VK_API_VERSION = Setting.get_value(key='VK_API_VERSION')


def delete_comment(api, owner_id, comment_id):
    try:
        api.wall.deleteComment(owner_id='-{}'.format(owner_id),
                               comment_id=comment_id,
                               api_version=VK_API_VERSION)
    except ApiError as error_msg:
        log.info('Group {} got api error in deleteComment method: {}'.format(owner_id, error_msg))


def prepare_id_white_list(white_list):
    white_list = re.sub('(id)', '', white_list)
    white_list = re.sub('[^\s\d]+', '-', white_list)
    return list(map(int, white_list.split()))


def does_group_exist(group_id):
    # TODO may be this is slow
    group = Group.objects.filter(Q(group_id=group_id) | Q(domain_or_id__contains=str(group_id))).first()
    return group


def get_callback_api_key(group_id):
    group = Group.objects.filter(Q(group_id=group_id) | Q(domain_or_id__contains=str(group_id))).first()
    token = group.callback_api_token

    log.debug('got callback token for group {}'.format(group_id))

    return token


def is_moderation_needed(from_id, group_id, white_list):
    log.debug('white list contains {}'.format(white_list))

    if str(from_id) == '-{}'.format(group_id):
        log.info('from_id {} is our group, cancel moderation'.format(from_id))
        return False

    if int(from_id) in white_list:
        log.info('from_id {} in white list, cancel moderation'.format(from_id))
        return False

    return True


def handle_comment_event(event_object, group_id):
    try:
        log.info('start handling comment {} in {} by {}'.format(event_object['id'], group_id, event_object['from_id']))

        group = Group.objects.select_related('user').filter(group_id=group_id).first()

        moderation_rule = ModerationRule.objects.first()
        white_list = prepare_id_white_list(moderation_rule.id_white_list)

        if not is_moderation_needed(event_object['from_id'], group_id, white_list):
            return False

        api = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id).get_api()
        if not api:
            log.warning('group {} no api created!'.format(group_id))
            return None

        words_stop_list = set(moderation_rule.words_stop_list.split())
        words_in_text = re.sub("[^\w]", " ", event_object['text']).split()

        all_checks = (checks.is_post_ad(api, event_object['post_id'], group_id),
                      checks.is_stop_words_in_text(words_stop_list, words_in_text),
                      checks.is_scam_words_in_text(words_in_text),
                      checks.is_video_in_attachments(event_object.get('attachments')),
                      checks.is_link_in_attachments(event_object.get('attachments')),
                      checks.is_group(event_object['from_id']),
                      checks.is_links_in_text(event_object['text']),
                      checks.is_vk_links_in_text(event_object['text']))

        if any(all_checks):
            delete_comment(api, group_id, event_object['id'])
            log.info('delete comment {} in {}'.format(event_object['id'], group_id))
            return True

        log.info('comment {} in {} was moderated, everything ok'.format(event_object['id'], group_id))
    except:
        log.error('error while rating', exc_info=True)
