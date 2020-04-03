from datetime import timedelta

from celery import shared_task
from constance import config
from django.utils import timezone

from posting.models import PostingHistory
from scraping.models import ScrapingHistory
import logging

log = logging.getLogger('posting.scheduled')


@shared_task(time_limit=120)
def delete_old_stat():
    log.info('delete_old_stat called')

    time_threshold = timezone.now() - timedelta(days=config.STATS_STORING_TIME)

    objects_to_delete = PostingHistory.objects.filter(created_at__lte=time_threshold)
    number_of_records, extended = objects_to_delete.delete()
    log.info(f'deleted {number_of_records} of posting history')

    objects_to_delete = ScrapingHistory.objects.filter(created_at__lte=time_threshold)
    number_of_records, extended = objects_to_delete.delete()
    log.info(f'deleted {number_of_records} of scraping history')

    log.info('delete_old_stat finished')
