import logging
from datetime import datetime, timedelta

from celery import shared_task
from constance import config
from django.utils import timezone

from posting.models import Group, AdRecord
from services.vk.auth_with_access_token import create_vk_session_with_access_token

log = logging.getLogger('posting.scheduled')


@shared_task
def delete_old_ads():
    log.info('delete_old_ads called')

    active_groups = Group.objects.filter(
        user__isnull=False,
        is_posting_active=True).distinct()

    for group in active_groups:

        hours = config.OLD_AD_RECORDS_HOURS
        time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=hours)

        ads = AdRecord.objects.filter(group=group, post_in_group_date__lt=time_threshold)
        log.debug('got {} ads in last 30 hours in group {}'.format(len(ads), group.group_id))

        if ads.exists():

            session = create_vk_session_with_access_token(group.user)
            if not session:
                continue

            api = session.get_api()
            if not api:
                continue

            ignore_ad_ids = []

            for ad in ads:
                if ad.ad_record_id == -1:
                    continue
                try:
                    resp = api.wall.delete(owner_id='-{}'.format(group.group_id),
                                           post_id=ad.ad_record_id)
                    log.debug('delete_old_ads {} response: {}'.format(ad.ad_record_id, resp))
                except:
                    log.error('got unexpected error in delete_old_ads for {}'.format(ad.ad_record_id), exc_info=True)
                    ignore_ad_ids.append(ad.id)
                    continue

            ads = ads.exclude(pk__in=ignore_ad_ids)
            number_of_records, extended = ads.delete()
            log.debug('delete {} ads out of db'.format(number_of_records))

    log.info('finish deleting old ads')
