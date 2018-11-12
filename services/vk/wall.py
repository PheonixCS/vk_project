import logging
from datetime import datetime, timedelta

from constance import config
from django.utils import timezone
from vk_requests.exceptions import VkAPIError

log = logging.getLogger('services.vk.wall')


def get_wall(api, group_id, count=20):
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
        log.error('group {} got api error: {}'.format(group_id, error_msg))
        return None

    return wall


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
        wall = [record for record in get_wall(api, group_id)['items']
                if record.get('marked_as_ads', False) and
                datetime.fromtimestamp(record['date'], tz=timezone.utc) >= time_threshold]

        if wall and wall[0].get('id', None) and wall[0].get('date', None):
            ad = {'id': wall[0].get('id'),
                  'date': wall[0].get('date')}
            log.debug('got ad with id {} in group {}'.format(ad['id'], group_id))
            return ad
    except:
        log.error('got unexpected error in get_ad_in_last_hour', exc_info=True)
