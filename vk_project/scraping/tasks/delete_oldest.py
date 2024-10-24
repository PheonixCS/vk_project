import logging

from celery import shared_task
from constance import config

from scraping.models import Donor, Record

log = logging.getLogger('scraping.scheduled')


@shared_task
def delete_oldest():
    log.debug('start deleting records')

    max_count = config.COMMON_RECORDS_COUNT_FOR_DONOR

    donors = Donor.objects.all()

    for donor in donors.iterator():
        records_number = Record.objects.filter(donor=donor).count()

        if records_number > max_count:
            records_to_delete_number = records_number - max_count

            all_records = Record.objects.filter(donor=donor).order_by('post_in_donor_date')
            ids_to_delete = all_records[:records_to_delete_number].values_list('id', flat=True)
            records_to_delete = all_records.filter(pk__in=ids_to_delete)

            number_of_records, extended = records_to_delete.delete()
            log.debug(f'deleted {number_of_records} records for group {donor.id}')

    log.debug('finish deleting records')
