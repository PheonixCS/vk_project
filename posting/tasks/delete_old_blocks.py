from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from posting.models import Block
import logging

log = logging.getLogger('posting.scheduled')


@shared_task(time_limit=10)
def delete_old_blocks():
    log.debug('delete_old_blocks called')

    time_threshold = timezone.now() - timedelta(days=3)

    objects_to_delete = Block.objects.filter(created_at__lte=time_threshold, is_active=False)
    number_of_records, extended = objects_to_delete.delete()
    log.info(f'deleted {number_of_records} of blocks')

    log.debug('delete_old_blocks finished')
    return number_of_records

