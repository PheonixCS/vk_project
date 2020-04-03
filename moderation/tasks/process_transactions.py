import logging

from celery import shared_task

from moderation.core.helpers import get_transactions_to_process, save_comment_to_db
from moderation.core.process_comment import process_comment
from moderation.models import WebhookTransaction

log = logging.getLogger('moderation.tasks')


@shared_task(time_limit=5)
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
