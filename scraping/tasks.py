#
import logging
from datetime import datetime, timedelta

from celery import task
from scraping.scraper import main
from scraping.models import Record


log = logging.getLogger('scraping.scheduled')


@task
def run_scraper():
    main()


@task
def delete_oldest():
    """
    Scheduled task for deleting records 2 weeks old

    :return:
    """
    # TODO add it to settings
    time_threshold = datetime.now() - timedelta(weeks=2)
    log.debug('start deleting records older than {}'.format(time_threshold))

    number_of_records, extended = Record.objects.filter(add_to_db_date__lt=time_threshold).delete()
    log.debug('deleted {} records'.format(number_of_records))
