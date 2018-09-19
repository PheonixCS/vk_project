import time
from datetime import datetime, timedelta

from constance import config
from django.utils import timezone
from vk_api import ApiError

from moderation.core.process_comment import log


def get_groups_by_id(api, group_ids, fields):
    try:
        return api.groups.getById(group_ids=group_ids,
                                  fields=fields,
                                  api_version=config.VK_API_VERSION)
    except ApiError as error_msg:
        log.info('api error in groups.getById method: {}'.format(error_msg))


def delete_comment(api, owner_id, comment_id):
    try:
        api.wall.deleteComment(owner_id='-{}'.format(owner_id),
                               comment_id=comment_id,
                               api_version=config.VK_API_VERSION)
    except ApiError as error_msg:
        log.info('group {} got api error in deleteComment method: {}'.format(owner_id, error_msg))


def ban_user(api, group_id, user_id, days_timedelta=None, comment=''):
    try:
        if days_timedelta:
            ban_end_date = datetime.now(tz=timezone.utc) + timedelta(days=days_timedelta)
            ban_end_date_timestamp = time.mktime(ban_end_date.timetuple())

            api.groups.ban(group_id=group_id,
                           owner_id=user_id,
                           end_date=ban_end_date_timestamp,
                           comment=comment,
                           api_version=config.VK_API_VERSION)
        else:
            api.groups.ban(group_id=group_id,
                           owner_id=user_id,
                           comment=comment,
                           api_version=config.VK_API_VERSION)
    except ApiError as error_msg:
        log.info('group {} got api error in ban method: {}'.format(group_id, error_msg))