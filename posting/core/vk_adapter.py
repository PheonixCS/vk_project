import logging
from typing import Optional, Type, TypeVar

import vk_api
from vk_api.vk_api import VkApiMethod, VkApi

from posting.core.vk_post_universal import VKUniversalPost
from posting.models import Group
from services.vk.auth_with_access_token import create_vk_session_with_access_token


log = logging.getLogger(__name__)
VKPost = TypeVar('VKPost', bound=VKUniversalPost)


class VKAdapter:
    def __init__(self, vk_group: Group):
        self.vk_group = vk_group

        self.__vk_session: Optional[VkApi] = None
        self.__vk_api: Optional[VkApiMethod] = None
        self.__vk_post_result = None

    def prepare_adapter(self) -> None:
        try:
            self.__vk_session = create_vk_session_with_access_token(self.vk_group.user)
            log.debug('Session created')

            self.__vk_api = self.__vk_session.get_api()
            log.debug('Api created')
        except vk_api.VkApiError:
            self.__vk_session = self.__vk_api = None
            log.error('Error while preparing vk adapter', exc_info=True)

    def is_ready(self) -> bool:
        return bool(self.__vk_session) and bool(self.__vk_api)

    def send_post(self, post: VKPost):
        data = post.data
        try:
            self.__vk_post_result = self.__vk_api.wall.post(**data)
        except vk_api.VkApiError:
            log.error(f'Error while posting {post}!', exc_info=True)
            self.__vk_post_result = False

        return self.__vk_post_result


