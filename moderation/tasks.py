import logging

from celery import task

from moderation.core import (get_transactions_to_process, process_comment, save_comment_to_db)
from moderation.models import WebhookTransaction

log = logging.getLogger('moderation.tasks')


@task
def process_transactions():
    log.info('start process_transactions task')

    unprocessed_transactions = get_transactions_to_process()
    log.info('got {} unprocessed comment transactions'.format(len(unprocessed_transactions)))

    try:
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
    except:
        log.error('', exc_info=True)

    log.info('process_transactions task completed')
