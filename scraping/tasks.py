#
import logging
from datetime import datetime, timedelta

from celery import task
from constance import config
from django.utils import timezone

from scraping.core.scraper import main
from scraping.models import Record, Horoscope

log = logging.getLogger('scraping.scheduled')


@task
def run_scraper():
    main()


@task
def delete_oldest():
    """
    Scheduled task for deleting records 24 hours old

    :return:
    """
    hours = config.OLD_RECORDS_HOURS
    time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    log.debug('start deleting records older than {}'.format(time_threshold))

    number_of_records, extended = Record.objects.filter(add_to_db_date__lt=time_threshold).delete()
    log.debug('deleted {} records'.format(number_of_records))


@task
def delete_old_horoscope_records():
    hours = config.OLD_HOROSCOPES_HOURS
    time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    log.debug('start deleting horoscope records older than {}'.format(time_threshold))

    number_of_records, extended = Horoscope.objects.filter(add_to_db_date__lt=time_threshold).delete()
    log.debug('deleted {} records'.format(number_of_records))

