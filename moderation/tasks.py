import logging
from random import choice

from celery import task

from posting.poster import create_vk_session_using_login_password
from posting.models import Group, ServiceToken
from moderation.core import (get_transactions_to_process, process_comment, save_comment_to_db, get_groups_by_id,
                             ban_user)
from moderation.models import WebhookTransaction

log = logging.getLogger('moderation.tasks')


@task
def process_transactions():
    log.info('start process_transactions task')

    unprocessed_transactions = get_transactions_to_process()
    log.info('got {} unprocessed comment transactions'.format(len(unprocessed_transactions)))

    for transaction in unprocessed_transactions:
        try:
            process_comment(transaction.body)
            save_comment_to_db(transaction)

            transaction.status = WebhookTransaction.PROCESSED
            transaction.save(update_fields=['status'])

        except:
            transaction.status = WebhookTransaction.ERROR
            transaction.save(update_fields=['status'])

            log.error('caught unexpected exception in process comment {}'.format(transaction.body['object']['id']),
                      exc_info=True)

    log.info('process_transactions task completed')


@task
def ban_donors_admins():
    log.info('start ban_donors_admins task')

    active_groups = Group.objects.filter(
        user__isnull=False,
        is_posting_active=True).distinct()

    for group in active_groups:
        donors_ids = [donor.id for donor in group.donors.all()]
        log.info(f'working with group {group.domain_or_id} donors {donors_ids}')

        api = create_vk_session_using_login_password(group.user.login, group.user.password,
                                                     group.user.app_id).get_api()

        donors = get_groups_by_id(api, donors_ids, fields='contacts')

        for donor in donors:
            for contact in donor.get('contacts', []):
                log.info(f'ban user {contact["user_id"]} in group {group.domain_or_id} : is admin in donor {donor.id}')
                ban_user(api, group.group_id, contact['user_id'])

    log.info('ban_donors_admins task completed')
