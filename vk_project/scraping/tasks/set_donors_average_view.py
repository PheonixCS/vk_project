import logging

from celery import shared_task
from constance import config
from django.db.models import Sum

from scraping.models import Donor, Record

log = logging.getLogger('scraping.scheduled')


@shared_task
def set_donors_average_view():
    log.debug('set_donors_average_view started')

    required_count = config.COMMON_RECORDS_COUNT_FOR_DONOR
    donors = Donor.objects.filter(is_involved=True, ban_reason__isnull=True)

    for donor in donors:
        if donor.records.count() < required_count:
            log.info(f'group {donor.id} has not enough records, skip')
            continue
        else:
            all_records = Record.objects.filter(donor=donor).order_by('-post_in_donor_date')[:required_count]
            views_count = all_records.aggregate(Sum('views_count')).get('views_count__sum')
            donor.average_views_number = views_count / required_count
            donor.save(update_fields=['average_views_number'])

    log.debug('set_donors_average_view finished')
