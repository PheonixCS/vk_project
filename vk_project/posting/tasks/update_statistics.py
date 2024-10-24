import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone

from posting.models import Group, ServiceToken, AdRecord
from scraping.models import Record, Horoscope, Movie
from services.vk.core import create_vk_api_using_service_token

log = logging.getLogger('posting.scheduled')
telegram = logging.getLogger('telegram')


@shared_task(time_limit=180, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3}, retry_backoff=120)
def update_statistics():
    log.debug('update_statistics called')

    now_time = datetime.now(tz=timezone.utc)
    today_start = now_time.replace(hour=0, minute=0, second=0)
    yesterday_start = today_start - timedelta(hours=24)

    all_groups = Group.objects.all()
    all_group_ids = all_groups.values_list('domain_or_id', flat=True)
    log.debug('got {} groups in update_statistics'.format(len(all_group_ids)))

    token = ServiceToken.objects.filter().first().app_service_token
    log.debug('using {} token for update_statistics'.format(token))

    api = create_vk_api_using_service_token(token)

    if not api:
        log.error('cannot update statistics')

    try:
        response = api.groups.getById(group_ids=all_group_ids, fields=['members_count'])

        for piece in response:

            screen_name = piece.get('screen_name', None)
            members_count_now = piece.get('members_count', None)
            group_id = piece.get('id', None)

            try:
                group = all_groups.get(domain_or_id=group_id)
            except ObjectDoesNotExist:
                group = all_groups.get(domain_or_id=screen_name)

            if group:
                members_count_last = group.members_count or 0
                group.members_growth = members_count_now - members_count_last
                group.members_count = members_count_now

                starts = Q(post_in_group_date__gte=yesterday_start)
                ends = Q(post_in_group_date__lte=today_start)

                group.number_of_posts_yesterday = \
                    Record.objects.filter(group_id=group.domain_or_id).filter(starts & ends).count() + \
                    Horoscope.objects.filter(group_id=group.domain_or_id).filter(starts & ends).count() + \
                    Movie.objects.filter(group_id=group.domain_or_id).filter(starts & ends).count()

                group.number_of_ad_posts_yesterday = AdRecord.objects.filter(group_id=group.domain_or_id). \
                    filter(starts & ends).count()

                group.statistics_last_update_date = now_time.strftime('%Y-%m-%d %H:%M:%S')

                group.save(update_fields=['members_growth',
                                          'members_count',
                                          'number_of_posts_yesterday',
                                          'number_of_ad_posts_yesterday',
                                          'statistics_last_update_date'])

                log.debug('finish updating statistic for group {} {}'.format(group_id, screen_name))
            else:
                log.warning('problem with group {} {}'.format(group_id, screen_name))

    except:
        log.debug('got unexpected error in update_statistics', exc_info=True)
        return

    log.debug('update_statistics finished successfully')
