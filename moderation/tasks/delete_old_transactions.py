import logging
from datetime import datetime, timedelta

from celery import shared_task
from constance import config
from django.utils import timezone

from moderation.models import WebhookTransaction

log = logging.getLogger('moderation.tasks')


@shared_task(time_limit=180)
def delete_old_transactions():
    hours = config.OLD_MODERATION_TRANSACTIONS_HOURS
    time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    log.debug(f'start deleting moderation transactions older than {time_threshold}')

    number_of_records, extended = WebhookTransaction.objects.filter(date_received__lt=time_threshold).delete()
    log.debug(f'deleted {number_of_records} transactions')
