import logging
from datetime import datetime, timedelta
from typing import Optional

import vk_api
from constance import config
from django.utils import timezone
from vk_requests.api import API
from vk_requests.exceptions import VkAPIError

from posting.models import Group, Block
from .vars import *

log = logging.getLogger('services.vk.wall')


def get_wall(api, group_id, count=20) -> (Optional[dict], Optional[str]):
    log.debug('get_wall api called for group {}'.format(group_id))

    version = config.VK_API_VERSION

    try:
        if group_id.isdigit():
            log.debug('group id is digit')
            wall = api.wall.get(
                owner_id=f'-{group_id}',
                filter='owner',
                api_version=version,
                count=count
            )
        else:
            log.debug('group id is not digit')
            wall = api.wall.get(
                domain=group_id,
                filter='owner',
                api_version=version,
                count=count
            )
    except VkAPIError as error_msg:
        reason = None
        if error_msg.message == BANNED_GROUP_ERROR_MESSAGE:
            reason = GROUP_IS_BANNED
        log.error('group {} got api error: {}'.format(group_id, error_msg))
        return None, reason

    except vk_api.ApiError as error_msg:
        reason = error_msg.error

        if error_msg.code == RATE_LIMIT_CODE:
            # FIXME пока создаём фейковую запись, но в будущем надо просто блочить
            group = Group.objects.get(group_id=group_id)
            block_result = group.set_block(reason=Block.RATE_LIMIT, period_in_minutes=5)
            log.info(f'Set block {block_result}')

        log.error('group {} got api error: {}'.format(group_id, error_msg))
        return None, reason

    return wall, None


def get_wall_by_post_id(api, group_id, posts_ids):
    log.debug('get_wall_by_post_id api called for group {}'.format(group_id))

    posts = [f'-{group_id}_{post}' for post in posts_ids]
    try:
        all_non_rated = api.wall.getById(
            posts=posts,
            api_version=config.VK_API_VERSION
        )
    except VkAPIError as error_msg:
        log.error('group {} got api error while : {}'.format(group_id, error_msg))
        return None

    return all_non_rated


def get_ad_in_last_hour(api, group_id):
    log.debug('get_ad_in_last_hour called')
    time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=1)

    try:
        wall, error = get_wall(api, group_id)
        if wall is None:
            log.warning(f'get_ad_in_last_hour failed with reason {error}')
            return True
        else:
            records = [record for record in wall['items']
                       if record.get('marked_as_ads', False) and
                       datetime.fromtimestamp(record['date'], tz=timezone.utc) >= time_threshold]

            if records and records[0].get('id', None) and records[0].get('date', None):
                ad = {'id': records[0].get('id'),
                      'date': records[0].get('date')}
                log.debug('got ad with id {} in group {}'.format(ad['id'], group_id))
                return ad
    except VkAPIError as error_msg:
        log.error('got unexpected error in get_ad_in_last_hour {}'.format(error_msg))


def get_records_info_from_groups(api: API, posts: list) -> dict:
    log.debug('get_records_info_from_groups called')
    try:
        all_non_rated = api.wall.getById(
            posts=posts,
            extended=1,
            copy_history_depth=0,
            api_version=config.VK_API_VERSION
        )
    except VkAPIError:
        log.error(f'error in get_records_info_from_groups', exc_info=True)
        return {}

    return all_non_rated
