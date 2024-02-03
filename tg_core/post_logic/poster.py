# posters factory
from typing import Union

from tg_core.tg_logic.adapter import TGUniversalPost


class VKAdapter:
    def __init__(self):
        raise NotImplementedError('VKAdapter is not implemented yet, it\'s just stub.')


class VKUniversalPost:
    def __init__(self):
        raise NotImplementedError('VKUniversalPost is not implemented yet, it\'s just stub.')


class Poster:
    def __init__(self):
        pass

    @staticmethod
    def post(post_object: Union[TGUniversalPost, VKUniversalPost]):
        post_object.prepare()
        post_object.post()
        return post_object
