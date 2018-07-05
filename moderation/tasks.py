import logging
import re

from celery import task

import moderation.checks as checks
from moderation.core import (get_transactions_to_process, prepare_id_white_list, is_moderation_needed, delete_comment, \
                             is_reason_for_ban_exists, ban_user)
from moderation.models import ModerationRule, WebhookTransaction
from posting.models import Group
from posting.poster import create_vk_session_using_login_password

log = logging.getLogger('moderation.tasks')


@task
def process_transactions():
    unprocessed_transactions = get_transactions_to_process()

    for transaction in unprocessed_transactions:
        process_comment.delay(transaction.id)


@task
def process_comment(transaction_id):
    log.info('process comment with transaction_id {} called'.format(transaction_id))

    transaction = WebhookTransaction.objects.filter(id=transaction_id)

    log.info('start handling comment {} in {} by {}'.format(transaction.body['id'],
                                                            transaction.body['group_id'],
                                                            transaction.body['from_id']))

    try:
        group = Group.objects.select_related('user').filter(group_id=transaction.body['group_id']).first()

        moderation_rule = ModerationRule.objects.first()
        white_list = prepare_id_white_list(moderation_rule.id_white_list)

        if not is_moderation_needed(transaction.body['from_id'], transaction.body['group_id'], white_list):
            return False

        api = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id).get_api()
        if not api:
            log.warning('group {} no api created!'.format(transaction.body['group_id']))
            return None

        words_stop_list = set(moderation_rule.words_stop_list.split())
        words_in_text = re.sub("[^\w]", " ", transaction.body['text']).split()

        all_checks = (checks.is_post_ad(api, transaction.body['post_id'], transaction.body['group_id']),
                      checks.is_stop_words_in_text(words_stop_list, words_in_text),
                      checks.is_scam_words_in_text(words_in_text),
                      checks.is_video_in_attachments(transaction.body.get('attachments')),
                      checks.is_link_in_attachments(transaction.body.get('attachments')),
                      checks.is_group(transaction.body['from_id']),
                      checks.is_links_in_text(transaction.body['text']),
                      checks.is_vk_links_in_text(transaction.body['text']),
                      checks.is_audio_and_photo_in_attachments(transaction.body.get('attachments')))

        if any(all_checks):
            delete_comment(api, transaction.body['group_id'], transaction.body['id'])
            log.info('delete comment {} in {}'.format(transaction.body['id'], transaction.body['group_id']))

            if is_reason_for_ban_exists(transaction.body):
                ban_user(api, transaction.body['group_id'], transaction.body['from_id'])
                log.info('ban user {} in {}'.format(transaction.body['from_id'], transaction.body['group_id']))

            return True

        log.info('comment {} in {} was moderated, everything ok'.format(transaction.body['id'],
                                                                        transaction.body['group_id']))

        transaction.status = WebhookTransaction.PROCESSED
        transaction.save(update_fields=['status'])

    except:
        transaction.status = WebhookTransaction.ERROR
        transaction.save(update_fields=['status'])

        log.error('caught unexpected exception in process comment {}'.format(transaction_id), exc_info=True)
