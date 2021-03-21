import logging

import vk_api
import vk_requests
from constance import config
from vk_requests.exceptions import VkAPIError
from .vars import BANNED_ACCOUNT_ERROR_MESSAGE

log = logging.getLogger('services.vk.core')
telegram = logging.getLogger('telegram')


def create_vk_session_using_login_password(login, password, app_id):
    log.debug('create_vk_session_using_login_password called')

    vk_session = vk_api.VkApi(login=login, password=password, app_id=app_id, api_version=config.VK_API_VERSION)
    try:
        vk_session.auth(token_only=True)
    except vk_api.AuthError as error_msg:
        log.info('User {} got api error: {}'.format(login, error_msg))
        if error_msg == BANNED_ACCOUNT_ERROR_MESSAGE:
            telegram.critical('Администратор с номером {} не смог залогиниться'.format(login))
        return None
    except:
        log.error('got unexpected error in create_vk_session_using_login_password', exc_info=True)

    return vk_session


def create_vk_api_using_service_token(token):
    log.debug('create_vk_api_using_service_token called')

    try:
        api = vk_requests.create_api(service_token=token, api_version=config.VK_API_VERSION)
    except VkAPIError as error_msg:
        log.error('token {} got api error: {}'.format(token, error_msg))
        telegram.critical('Ошибка с токеном {}: {}'.format(token, error_msg))
        return None

    return api


def fetch_group_id(api, domain_or_id):
    log.debug('fetch_group_id called for group {}'.format(domain_or_id))

    if domain_or_id.isdigit():
        group_id = domain_or_id
    else:
        try:
            group_id = api.utils.resolveScreenName(domain_or_id).get('object_id')
        except:
            log.error('got exception while fetching group id', exc_info=True)
            return None

    return group_id
