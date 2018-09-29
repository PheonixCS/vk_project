import logging
from datetime import datetime, timedelta

from celery import task
from constance import config
from django.utils import timezone

from moderation.core.helpers import get_transactions_to_process, save_comment_to_db
from moderation.core.process_comment import process_comment
from moderation.core.vk_helpers import get_groups_by_id, ban_user
from moderation.models import WebhookTransaction
from posting.models import Group
from posting.poster import create_vk_session_using_login_password

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
                log.info(f'ban user {contact["user_id"]} in group {group.domain_or_id} : '
                         f'is admin in donor {donor.get("id")}')
                ban_user(api, group.group_id, contact['user_id'], comment=f'Администратор в источнике {donor.id}')

    log.info('ban_donors_admins task completed')


@task
def delete_old_transactions():
    hours = config.OLD_MODERATION_TRANSACTIONS_HOURS
    time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    log.debug(f'start deleting moderation transactions older than {time_threshold}')

    number_of_records, extended = WebhookTransaction.objects.filter(date_received__lt=time_threshold).delete()
    log.debug(f'deleted {number_of_records} transactions')
