import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from posting.models import Group
from scraping.core.scraping_history import save_filter_stats
from scraping.models import Record
from services.vk.auth_with_access_token import create_vk_session_with_access_token
from services.vk.files import check_video_availability

log = logging.getLogger('scraping.scheduled')


@shared_task(time_limit=180)  # 3 minutes limit
def check_attachments_availability() -> None:
    log.debug('start check_attachments_availability')

    groups = Group.objects.filter(group_type__in=(Group.COMMON, Group.MOVIE_COMMON))
    allowed_time_threshold = timezone.now() - timedelta(hours=8)

    for group in groups:
        records = Record.objects.filter(
            rate__isnull=False,
            status=Record.READY,
            post_in_group_date__isnull=True,
            failed_date__isnull=True,
            post_in_donor_date__gt=allowed_time_threshold,
            donor__in=group.donors.all()
        )
        log.debug(f'got {len(records)} records in group {group.group_id} before check_attachments_availability')

        if records:
            session = create_vk_session_with_access_token(group.user)
            api = session.get_api()
        else:
            continue

        filtered = 0
        for record in records:
            for video in record.videos.all():
                if check_video_availability(api, video.owner_id, video.video_id):
                    continue
                else:
                    record.set_failed()
                    filtered += 1

                    save_filter_stats(record.donor, 'check_attachments_availability', 1)
                    break

        log.debug(f'filtered {filtered} records in group {group.group_id} after check_attachments_availability')

    log.debug('finish check_attachments_availability')
