from datetime import datetime, timedelta

from constance import config
from django.utils import timezone
from vk_requests.exceptions import VkAPIError

import logging


log = logging.getLogger('services.vk.stat')


def get_group_week_statistics(api, group_id):

    now = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d')
    week_ago = (datetime.now(tz=timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')

    print(now, week_ago)

    return api.stats.get(group_id=group_id, date_from=week_ago, date_to=now)


def fetch_liked_user_ids(api, group_id, post_id):
    log.debug('fetch_liked_user_ids api called for group {}'.format(group_id))

    try:
        likes_list = api.likes.getList(
            type='post',
            owner_id='-{}'.format(group_id),
            item_id=post_id,
            filter='likes',
            extended=1,  # needed for user type, we need just profile
            api_version=config.VK_API_VERSION
            )

    except VkAPIError as error_msg:
        log.error('group {} got api error while : {}'.format(group_id, error_msg))
        return None

    log.debug('got {} likes list'.format(likes_list.get('count')))
    # TODO think what is default in .get('id')
    ids_list = [profile.get('id', 0) for profile in likes_list['items'] if profile.get('type', '') == 'profile']
    log.debug('got {} likes after extracting'.format(len(ids_list)))

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