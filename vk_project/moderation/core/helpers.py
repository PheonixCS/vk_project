import logging
import re

from django.db.models import Q

from moderation.models import WebhookTransaction, Comment, Attachment
from posting.models import Group
from typing import List

log = logging.getLogger('moderation.core.helpers')


def get_transactions_to_process():
    event_types = ['wall_reply_new', 'wall_reply_edit', 'wall_reply_restore']
    return WebhookTransaction.objects.filter(
        body__type__in=event_types,
        status=WebhookTransaction.UNPROCESSED
    )


def prepare_id_white_list(white_list):
    white_list = re.sub(r'(id)', '', white_list)
    white_list = re.sub(r'[^\s\d]+', '-', white_list)
    return list(map(int, white_list.split()))


def does_group_exist(group_id):
    return Group.objects.filter(Q(group_id=group_id) | Q(domain_or_id__contains=str(group_id))).first()


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


def group_transactions_by_group_id(transactions: List[WebhookTransaction]) -> dict:
    result = dict()

    for tr in transactions:
        group_id = tr.body.get('group_id')
        if group_id:
            tr_by_group = result.get(group_id, [])
            tr_by_group.append(tr)
            result[group_id] = tr_by_group

    return result
