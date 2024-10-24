import logging
from datetime import timedelta
from time import sleep

import vk_api
import vk_requests
from constance import config
from django.utils import timezone
from requests import Session
from vk_requests.exceptions import VkAPIError

from posting.models import User, AuthCode
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

    user_object = User.objects.get(login=login)
    log.debug(f'Working with {user_object}')

    # use this custom session for debug requests for vk
    if special_session:
        custom_session = CustomSession()
    else:
        custom_session = Session()

    if user_object.two_factor and user_object.is_authed is False:
        log.warning(f'User {user_object} need two factor auth')
        return None

    if config.USE_APP:
        vk_session = vk_api.VkApi(login=login, password=password, api_version=config.VK_API_VERSION,
                                  session=custom_session, app_id=app_id)
    else:
        vk_session = vk_api.VkApi(login=login, password=password, api_version=config.VK_API_VERSION,
                                  session=custom_session)

    try:
        vk_session.http.headers[
            'User-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'

        log.debug('auth start')
        vk_session.auth(token_only=True)
        log.debug('auth end')

    except vk_api.TwoFactorError as err:
        log.warning(f'User {login} got two-factor error {err}')
        user_object.is_authed = False
        return None

    except vk_api.AuthError as error_msg:
        log.info('User {} got api error: {}'.format(login, error_msg))
        if error_msg == BANNED_ACCOUNT_ERROR_MESSAGE:
            telegram.critical('Администратор с номером {} не смог залогиниться'.format(login))
        return None

    except:
        log.error('got unexpected error in create_vk_session_using_login_password', exc_info=True)
        return None

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


def custom_auth_handler(user: User):
    log.debug('start')
    remember_device = True

    now = timezone.now() - timedelta(minutes=5)

    success = False
    key = ''
    try_num = 1
    max_tries = 10

    while not success and try_num < max_tries:
        code_object = AuthCode.objects.filter(user=user, create_dt__gte=now, used=False).order_by('-create_dt').first()

        if code_object is None:
            log.debug('Code is None')
        else:
            log.debug(code_object)

            key = code_object.code

            code_object.used = True
            code_object.save()
            break

        try_num += 1
        sleep(30)

    if try_num >= max_tries:
        raise vk_api.TwoFactorError('No code')

    log.debug(f'end with key: {key}')
    return key, remember_device


def activate_two_factor(user_object):
    # app_id=user_object.app_id
    vk_session = vk_api.VkApi(login=user_object.login, password=user_object.password,
                              api_version=config.VK_API_VERSION,
                              auth_handler=lambda: custom_auth_handler(user_object))

    try:
        vk_session.auth()
        user_object.is_authed = True

    except vk_api.AuthError as err:
        log.warning(f'User {user_object} got auth error {err}')
        user_object.is_authed = False

    # just for test
    # data_to_post = {
    #     'owner_id': f'-{166051711}',
    #     'from_group': 1,
    #     'message': 'test',
    # }
    #
    # post_response = vk_session.get_api().wall.post(**data_to_post)
    # log.debug(post_response)

    user_object.save()

    return user_object.is_authed
