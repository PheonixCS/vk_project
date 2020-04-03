import logging
from datetime import datetime, timedelta

from celery import shared_task
from constance import config
from django.utils import timezone

from posting.models import ServiceToken
from scraping.core.helpers import extract_records_per_donor
from scraping.core.scraper import update_structured_records
from scraping.core.vk_helper import get_records_info, extract_records_sex
from scraping.models import Record
from services.vk.core import create_vk_api_using_service_token

log = logging.getLogger('scraping.scheduled')


@shared_task(time_limit=300)  # 5 minutes limit
def rate_new_posts() -> None:
    log.debug('rating started')
    threshold = datetime.now(tz=timezone.utc) - timedelta(minutes=config.NEW_RECORD_MATURITY_MINUTES)

    new_token = ServiceToken.objects.filter(last_used__isnull=True)
    if new_token:
        token = new_token.first()
    else:
        token = ServiceToken.objects.order_by('last_used').first()

    token.last_used = timezone.now()
    token.save(update_fields=['last_used'])

    log.debug(f'Using {token.app_service_token} token for rate_new_posts')

    api = create_vk_api_using_service_token(token.app_service_token)
    if not api:
        log.error('cannot rate new posts')
        return

    new_records = Record.objects.filter(status=Record.NEW, post_in_donor_date__lte=threshold)
    log.info(f'got {new_records.count()} new records')

    if new_records:
        i = 0
        while i < new_records.count():
            records_info = get_records_info(api, new_records[i: i + 100])
            structured_records = extract_records_per_donor(records_info)
            extract_records_sex(api, structured_records)
            update_structured_records(structured_records)
            i += 100

    log.debug('rating finished')
