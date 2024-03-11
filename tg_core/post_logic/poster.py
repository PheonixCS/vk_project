# posters factory
from typing import Union

from posting.core.vk_post_universal import VKUniversalPost
from tg_core.tg_logic.adapter import TGUniversalPost


class Poster:
    @staticmethod
    def post(post_object: Union[TGUniversalPost, VKUniversalPost]):
        post_object.prepare()
        post_object.post()
        return post_object
