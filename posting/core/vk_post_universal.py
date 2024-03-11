import logging
from typing import Optional, Union

from posting.core.vk_adapter import VKAdapter
from posting.models import Group
from scraping.models import Record
from tg_core.post_logic.universal_post import UniversalPost

log = logging.getLogger('posting.vk')


class VKUniversalPost(UniversalPost):
    def __init__(self, vk_record_object: Record, target_group: Group):
        super().__init__()

        self.data: Optional[dict] = None

        self.__vk_record = vk_record_object
        self.__target_group = target_group
        self.__adapter = VKAdapter(target_group)

    @property
    def vk_record(self):
        return self.__vk_record

    @property
    def adapter(self):
        return self.__adapter

    def _prepare(self) -> bool:
        if not self.__adapter.is_ready():
            self.__adapter.prepare_adapter()

        return self.__adapter.is_ready() and self.data

    def _post_failed_hook(self) -> None:
        pass

    def _post_succeeded_hook(self) -> None:
        pass

    def _post(self) -> Union[dict, bool]:
        return self.__adapter.send_post(self)

