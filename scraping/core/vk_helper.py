#

import logging

import vk_requests
from constance import config
from vk_requests.exceptions import VkAPIError

log = logging.getLogger('scraping.core.vk_api_helpers')


def create_vk_api_using_service_token(token):
    log.debug('create api called')

    try:
        api = vk_requests.create_api(service_token=token, api_version=config.VK_API_VERSION)
    except VkAPIError as error_msg:
        log.warning('token {} got api error: {}'.format(token, error_msg))
        return None

    return api


def get_wall(api, group_id, count=20):
    log.debug('get_wall api called for group {}'.format(group_id))

    try:
        if group_id.isdigit():
            log.debug('group id is digit')
            wall = api.wall.get(owner_id='-{}'.format(group_id),
                                filter='owner',
                                api_version=config.VK_API_VERSION,
                                count=count)
        else:
            log.debug('group id os not digit')
            wall = api.wall.get(domain=group_id,
                                filter='owner',
                                api_version=config.VK_API_VERSION,
                                count=count)
    except VkAPIError as error_msg:
        log.warning('group {} got api error: {}'.format(group_id, error_msg))
        return None

    return wall


def get_wall_by_post_id(api, group_id, posts_ids):
    log.debug('get_wall_by_post_id api called for group {}'.format(group_id))

    posts = ['-{}_{}'.format(group_id, post) for post in posts_ids]
    try:
        all_non_rated = api.wall.getById(posts=posts,
                                         api_version=config.VK_API_VERSION)
    except VkAPIError as error_msg:
        log.warning('group {} got api error while : {}'.format(group_id, error_msg))
        return None

    return all_non_rated


def get_post_likes_by_id(api, group_id, post_id):
    log.debug('get_post_likes_by_id api called for group {}'.format(group_id))

    try:
        likes_list = api.likes.getList(
            type='post',
            owner_id='-{}'.format(group_id),
            item_id=post_id,
            filter='likes',
            extndet=1,  # needed for user type, we need just profile
            api_version=config.VK_API_VERSION
            )

    except VkAPIError as error_msg:
        log.warning('group {} got api error while : {}'.format(group_id, error_msg))
        return None

    return likes_list


def get_users_sex_by_ids(api, user_ids):
    log.debug('get_users_sex_by_ids called')

    try:
        users_sex_list = api.users.get(
            user_ids=user_ids,
            fields='sex'
        )
    except VkAPIError as error_msg:
        log.warning('got api error while : {}'.format(error_msg))
        return None

    return users_sex_list
