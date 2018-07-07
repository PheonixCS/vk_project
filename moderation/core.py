import logging
import re
import time
from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone
from vk_api import ApiError

import moderation.checks as checks
from moderation.models import WebhookTransaction, ModerationRule, Comment, Attachment
from posting.models import Group
from posting.poster import create_vk_session_using_login_password
from settings.models import Setting

log = logging.getLogger('moderation.core')

VK_API_VERSION = Setting.get_value(key='VK_API_VERSION')


def get_transactions_to_process():
    event_types = ['wall_reply_new', 'wall_reply_edit', 'wall_reply_restore']
    return WebhookTransaction.objects.filter(
        body__type__in=event_types,
        status=WebhookTransaction.UNPROCESSED
    )


def delete_comment(api, owner_id, comment_id):
    try:
        api.wall.deleteComment(owner_id='-{}'.format(owner_id),
                               comment_id=comment_id,
                               api_version=VK_API_VERSION)
    except ApiError as error_msg:
        log.info('group {} got api error in deleteComment method: {}'.format(owner_id, error_msg))


def ban_user(api, group_id, user_id):
    ban_end_date = datetime.now(tz=timezone.utc) + timedelta(days=7)
    ban_end_date_timestamp = time.mktime(ban_end_date.timetuple())

    try:
        api.groups.ban(group_id=group_id,
                      owner_id=user_id,
                      end_date=ban_end_date_timestamp,
                      api_version=VK_API_VERSION)
    except ApiError as error_msg:
        log.info('group {} got api error in ban method: {}'.format(group_id, error_msg))


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


def is_reason_for_ban_and_get_comments_to_delete(event_object):
    if checks.is_group(event_object['from_id']):
        log.info('from_id {} reason for ban: is group'.format(event_object['from_id']))
        return True, event_object['id']

    if checks.is_audio_and_photo_in_attachments(event_object.get('attachments', [])):
        log.info('from_id {} reason for ban: audio + photo in attachments'.format(event_object['from_id']))
        return True, event_object['id']

    # FIXME timedelta
    time_threshold = datetime.now(tz=timezone.utc) - timedelta(minutes=10)
    time_threshold_timestamp = time.mktime(time_threshold.timetuple())

    if event_object['text']:
        comments_with_same_text = Comment.objects.filter(
            post_owner_id=event_object['post_owner_id'],
            from_id=event_object['from_id'],
            text=event_object['text'],
            date__gt=time_threshold_timestamp
        )
        if len(comments_with_same_text) >= 2:
            log.info('from_id {} reason for ban: >3 comments with same text'.format(event_object['from_id']))
            return True, [c.comment_id for c in comments_with_same_text].append(event_object['id'])

    for attachment in event_object.get('attachments', []):
        comments_from_user = Comment.objects.filter(
            post_owner_id=event_object['post_owner_id'],
            from_id=event_object['from_id'],
            date__gt=time_threshold_timestamp
        )

        comments_with_same_attachment = [c.comment_id for c in comments_from_user if
                                         c.attachments.filter(body__id=attachment[attachment['type']]['id']).exists()]
        log.debug('comments with same attachments {}'.format(comments_with_same_attachment))

        if len(comments_with_same_attachment) >= 2:
            log.info('from_id {} reason for ban: >3 comments with same attachment'.format(event_object['from_id']))
            return True, comments_with_same_attachment.append(event_object['id'])

    log.info('no reason for ban user {}'.format(event_object['from_id']))
    return False, []


def save_comment_to_db(transaction):
    log.info('save_comment_to_db called')
    obj = Comment.objects.create(
        webhook_transaction=transaction,
        post_id=transaction.body['object']['post_id'],
        post_owner_id=transaction.body['object']['post_owner_id'],
        comment_id=transaction.body['object']['id'],
        from_id=transaction.body['object']['from_id'],
        date=transaction.body['object']['date'],
        text=transaction.body['object']['text'],
        reply_to_user=transaction.body['object'].get('reply_to_user'),
        reply_to_comment=transaction.body['object'].get('reply_to_comment')
    )
    for attachment in transaction.body['object'].get('attachments', []):
        Attachment.objects.create(
            attached_to=obj,
            type=attachment['type'],
            body=attachment[attachment['type']]
        )


def process_comment(comment):
    log.info('start handling comment {} in {} by {}'.format(comment['object']['id'],
                                                            comment['group_id'],
                                                            comment['object']['from_id']))

    group = Group.objects.select_related('user').filter(group_id=comment['group_id']).first()

    moderation_rule = ModerationRule.objects.first()
    white_list = prepare_id_white_list(moderation_rule.id_white_list)

    if not is_moderation_needed(comment['object']['from_id'], comment['group_id'], white_list):
        return False

    api = create_vk_session_using_login_password(group.user.login, group.user.password,
                                                 group.user.app_id).get_api()
    if not api:
        log.warning('group {} no api created!'.format(comment['group_id']))
        return None

    words_stop_list = set(moderation_rule.words_stop_list.split())
    words_in_text = re.sub("[^\w]", " ", comment['object']['text']).split()

    all_checks = (checks.is_post_ad(api, comment['object']['post_id'], comment['group_id']),
                  checks.is_stop_words_in_text(words_stop_list, words_in_text),
                  checks.is_scam_words_in_text(words_in_text),
                  checks.is_video_in_attachments(comment['object'].get('attachments', [])),
                  checks.is_link_in_attachments(comment['object'].get('attachments', [])),
                  checks.is_group(comment['object']['from_id']),
                  checks.is_links_in_text(comment['object']['text']),
                  checks.is_vk_links_in_text(comment['object']['text']),
                  checks.is_audio_and_photo_in_attachments(comment['object'].get('attachments', [])))

    reason_for_ban, comments_to_delete = is_reason_for_ban_and_get_comments_to_delete(comment['object'])
    if reason_for_ban:
        ban_user(api, comment['group_id'], comment['object']['from_id'])
        log.info('ban user {} in {}'.format(comment['object']['from_id'], comment['group_id']))

        for comment_to_delete_id in comments_to_delete:
            delete_comment(api, comment['group_id'], comment_to_delete_id)
            log.info('delete comment {} in {}'.format(comment['object']['id'], comment['group_id']))

        return True

    if any(all_checks):
        delete_comment(api, comment['group_id'], comment['object']['id'])
        log.info('delete comment {} in {}'.format(comment['object']['id'], comment['group_id']))
        return True

    log.info('comment {} in {} was moderated, everything ok'.format(comment['object']['id'],
                                                                    comment['group_id']))
