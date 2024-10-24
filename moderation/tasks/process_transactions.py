import logging

from celery import shared_task

from moderation.core.helpers import get_transactions_to_process, save_comment_to_db, group_transactions_by_group_id
from moderation.core.process_comment import process_comment
from moderation.models import WebhookTransaction
from posting.models import Group
from moderation.core.token import GetAuthToken

log = logging.getLogger('moderation.tasks')


@shared_task(time_limit=60)
def process_transactions():
    log.info('start process_transactions task')

    unprocessed_transactions = get_transactions_to_process()
    log.info('got {} unprocessed comment transactions'.format(len(unprocessed_transactions)))

    grouped_transaction = group_transactions_by_group_id(unprocessed_transactions)

    for group_id in grouped_transaction.keys():
        group = Group.objects.select_related('user').filter(group_id=group_id).first()
        log.info('start creating creds')
        #session=create_vk_session_using_login_password(login=group.user.login, password=group.user.password, app_id=group.user.app_id)
        manager = GetAuthToken()
        token = manager.get_actual_token(app_id=52061491)
        
        log.info('finish creating creds')

        for transaction in grouped_transaction[group_id]:
            try:
                process_comment(transaction.body, token=token)
                save_comment_to_db(transaction)

                transaction.status = WebhookTransaction.PROCESSED
                transaction.save(update_fields=['status'])

            except:
                transaction.status = WebhookTransaction.ERROR
                transaction.save(update_fields=['status'])

                log.error('caught unexpected exception in process comment {}'.format(transaction.body['object']['id']),
                          exc_info=True)

    log.info('process_transactions task completed')
