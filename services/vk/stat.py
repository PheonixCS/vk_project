import logging
from datetime import datetime, timedelta
import time

from constance import config
from django.utils import timezone
from vk_requests.exceptions import VkAPIError

log = logging.getLogger('services.vk.stat')


def get_group_week_statistics(api, group_id):
    log.debug('get_group_week_statistics called for group {}'.format(group_id))
    now = datetime.now(tz=timezone.utc)
    week_ago = (datetime.now(tz=timezone.utc) - timedelta(days=7))

    now = int(time.mktime(now.timetuple()))
    week_ago = int(time.mktime(week_ago.timetuple()))

    return api.stats.get(group_id=group_id, timestamp_from=week_ago, timestamp_to=now)


def fetch_liked_user_ids(api, group_id, post_id):
    log.debug('fetch_liked_user_ids api called for group {}'.format(group_id))

    try:
        likes_list = api.likes.getList(
            type='post',
            owner_id=f'-{group_id}',
            item_id=post_id,
            filter='likes',
            count=1000,
            extended=1,  # needed for user type, we need just profile
            api_version=config.VK_API_VERSION
            )
    except VkAPIError as error_msg:
        log.error('group {} got api error while : {}'.format(group_id, error_msg))
        return None

    log.debug('got {} likes list'.format(likes_list.get('count')))

    ids_list = [profile.get('id') for profile in likes_list['items']
                if profile.get('type', '') == 'profile'
                and profile.get('id', None)]

    log.debug('got {} likes after filter non profiles and without id'.format(len(ids_list)))
    return ids_list


def get_users_sex_by_ids(api, user_ids):
    log.debug('get_users_sex_by_ids called')

    try:
        users_info_list = api.users.get(
            user_ids=user_ids,
            fields='sex'
        )
    except VkAPIError as error_msg:
        log.error('got api error while : {}'.format(error_msg))
        return None

    sex_list = [int(profile.get('sex', 0)) for profile in users_info_list]

    return sex_list
