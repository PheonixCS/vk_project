# posters factory
from typing import Union

from tg_core.tg_logic.adapter import TGUniversalPost


class VKAdapter:
    raise NotImplemented('VKAdapter is not implemented yet, it\'s just stub.')


class VKUniversalPost:
    raise NotImplemented('VKUniversalPost is not implemented yet, it\'s just stub.')


class Poster:
    def __init__(self, channel: int):
        self.channel = channel

    def post(self, post_object: Union[TGUniversalPost, VKUniversalPost]):
        post_object.prepare()
        post_object.post(self.channel)
        return post_object
