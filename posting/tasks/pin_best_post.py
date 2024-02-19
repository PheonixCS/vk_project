import logging
from datetime import datetime, timedelta
from random import choice

from celery import shared_task
from constance import config
from django.utils import timezone

from posting.models import Group, ServiceToken
from services.vk.auth_with_access_token import create_vk_session_with_access_token
from services.vk.core import create_vk_api_using_service_token, fetch_group_id
from services.vk.wall import get_wall

log = logging.getLogger('posting.scheduled')


@shared_task
def pin_best_post():
    """

    :return:
    """

    active_groups = Group.objects.filter(
        user__isnull=False,
        is_posting_active=True,
        is_pin_enabled=True).distinct()

    tokens = [token.app_service_token for token in ServiceToken.objects.all()]
    log.info('working with {} tokens: {}'.format(len(tokens), tokens))

    if not tokens:
        log.error('Got no tokens!')
        return

    for group in active_groups:
        token = choice(tokens)
        log.debug('work with token {}'.format(token))
        search_api = create_vk_api_using_service_token(token)
        time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=24)
        log.debug('search for posts from {} to now'.format(time_threshold))

        records_count = config.WALL_RECORD_COUNT_TO_PIN
        wall, error = get_wall(search_api, group.domain_or_id, count=records_count)
        records = [record for record in wall['items']
                   if datetime.fromtimestamp(record['date'], tz=timezone.utc) >= time_threshold]

        if records:
            log.debug('got {} wall records in last 24 hours'.format(len(records)))

            try:
                best = max(records, key=lambda item: item['views']['count'])
            except KeyError:
                log.error('failed to fetch best record', exc_info=True)
                continue
            log.debug('got best record with id: {}'.format(best['id']))

            session = create_vk_session_with_access_token(group.user)
            if not session:
                continue

            api = session.get_api()
            if not api:
                continue

            group.group_id = fetch_group_id(api, group.domain_or_id)
            group.save(update_fields=['group_id'])

            try:
                response = api.wall.pin(owner_id='-{}'.format(group.group_id),
                                        post_id=best['id'])
                log.debug(response)
            except:
                log.error('failed to pin post', exc_info=True)
                continue

        else:
            log.warning('have no post in last 24 hours')
            continue
