import logging
import re
import time
from datetime import datetime, timedelta

from django.utils import timezone

import moderation.core.checks as checks
from moderation.core.helpers import prepare_id_white_list, is_moderation_needed
from moderation.core.vk_helpers import delete_comment, ban_user
from moderation.models import ModerationRule, Comment
from posting.models import Group
from services.vk.core import create_vk_session_using_login_password

log = logging.getLogger('moderation.core.process_comment')


def check_for_reason_for_ban_and_get_comments_to_delete(event_object):
    if checks.is_group(event_object['from_id']):
        log.info('from_id {} reason for ban: is group'.format(event_object['from_id']))
        return 'группа', [event_object['id']]

    if checks.is_audio_and_photo_in_attachments(event_object.get('attachments', [])):
        log.info('from_id {} reason for ban: audio + photo in attachments'.format(event_object['from_id']))
        return 'фото + аудио во вложении', [event_object['id']]

    time_threshold = datetime.now(tz=timezone.utc) - timedelta(days=1)
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
            comments_to_delete = [c.comment_id for c in comments_with_same_text]
            comments_to_delete.append(event_object['id'])
            return '>3 комментариев с одинаковым текстом', comments_to_delete

    for attachment in event_object.get('attachments', []):
        comments_from_user = Comment.objects.filter(
            post_owner_id=event_object['post_owner_id'],
            from_id=event_object['from_id'],
            date__gt=time_threshold_timestamp
        )

        comments_with_same_attachment = []
        if attachment[attachment['type']].get('id'):
            comments_with_same_attachment = [c.comment_id for c in comments_from_user if
                                             c.attachments.filter(
                                                 body__id=attachment[attachment['type']]['id']).exists()]
        elif attachment[attachment['type']].get('url'):
            comments_with_same_attachment = [c.comment_id for c in comments_from_user if
                                             c.attachments.filter(
                                                 body__url=attachment[attachment['type']]['url']).exists()]

        log.debug('comments with same attachments {}'.format(comments_with_same_attachment))

        if len(comments_with_same_attachment) >= 2:
            log.info('from_id {} reason for ban: >3 comments with same attachment'.format(event_object['from_id']))
            comments_to_delete = comments_with_same_attachment
            comments_to_delete.append(event_object['id'])
            return '>3 комментариев с одинаковым вложением', comments_to_delete

    log.info('no reason for ban user {}'.format(event_object['from_id']))
    return '', []


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

    reason_for_ban, comments_to_delete = check_for_reason_for_ban_and_get_comments_to_delete(comment['object'])
    if reason_for_ban:
        ban_user(api, comment['group_id'], comment['object']['from_id'], days_timedelta=7, comment=reason_for_ban)
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
