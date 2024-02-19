import logging
from typing import Optional

import vk_api
from constance import config

from posting.models import User

DEF_SCOPES = 'wall,offline,stats'
VK_AUTH_URL = 'https://oauth.vk.com/authorize'
REDIRECT_URL = 'https://oauth.vk.com/blank.html'

log = logging.getLogger(__name__)


def create_vk_session_with_access_token(user: User) -> Optional[vk_api.VkApi]:
    log.debug(f'start session creation with token for {user}')

    vk_session = None
    data = dict(
        access_token=user.access_token,
        application_id=user.app_id,
        api_version=config.VK_API_VERSION,
        scopes=DEF_SCOPES,
    )

    data_is_filled = all(len(str(value)) for value in data.values())
    if data_is_filled:
        try:
            vk_session = vk_api.VkApi(**data)
        except vk_api.VkApiError:
            log.error(
                f'VK api error while creating session with user access token for {user}',
                exc_info=True
            )
    else:
        log.error(f'Data for creation is not filled for {user}: {data}')

    log.debug(f'finish creating session for {user}')
    return vk_session


def generate_url_for_access_token_generation(user: User) -> str:
    log.debug(f'start access token url generation for {user}')

    data = dict(
        client_id=user.app_id,
        redirect_uri=REDIRECT_URL,
        display='mobile',
        scope=DEF_SCOPES,
        response_type='token',
        revoke=1
    )

    url_result = f'{VK_AUTH_URL}?' + '&'.join(
        [f'{key}={value}' for key, value in data.items()]
    )
    log.debug(f'finish token generation for {user}')
    return url_result
