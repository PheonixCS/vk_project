import logging
from datetime import datetime, timedelta

from celery import shared_task
from constance import config
from django.utils import timezone

from scraping.models import Horoscope

log = logging.getLogger('scraping.scheduled')


@shared_task
def delete_old_horoscope_records():
    hours = config.OLD_HOROSCOPES_HOURS
    time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    log.debug('start deleting horoscope records older than {}'.format(time_threshold))

    number_of_records, extended = Horoscope.objects.filter(add_to_db_date__lt=time_threshold).delete()
    log.debug('deleted {} records'.format(number_of_records))
