import logging

import vk_api
import vk_requests
from constance import config
from requests import Session
from vk_requests.exceptions import VkAPIError
from .vars import BANNED_ACCOUNT_ERROR_MESSAGE

log = logging.getLogger('services.vk.core')
telegram = logging.getLogger('telegram')


class CustomSession(Session):
    def prepare_request(self, *args, **kwargs):
        result = super().prepare_request(*args, **kwargs)
        actual_request = '{}\n{}\r\n{}\r\n\r\n{}'.format(
            '-----------START-----------',
            result.method + ' ' + result.url,
            '\r\n'.join('{}: {}'.format(k, v) for k, v in result.headers.items()),
            result.body,
        )
        log.debug(actual_request)
        return result


def create_vk_session_using_login_password(login, password, app_id, special_session=False):
    log.debug('create_vk_session_using_login_password called')

    # use this custom session for debug requests for vk
    if special_session:
        custom_session = CustomSession()
    else:
        custom_session = Session()

    vk_session = vk_api.VkApi(login=login, password=password, app_id=app_id, api_version=config.VK_API_VERSION,
                              session=custom_session)
    try:
        vk_session.http.headers[
            'User-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:94.0) Gecko/20100101 Firefox/94.0'
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
