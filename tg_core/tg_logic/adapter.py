# tg posting adapter
import logging
from typing import Union, Optional

import telegram
from asgiref.sync import async_to_sync
from django.utils import timezone

from tg_core.models.tg_attachment import TGAttachment
from tg_core.models.tg_post import TGPost
from tg_core.post_logic.universal_post import UniversalPost
from tg_core.tg_logic.bot import get_bot

log = logging.getLogger()


class TGAdapter:
    def __init__(self, bot_token=None):
        self.__bot = get_bot(bot_token) if bot_token else get_bot()

    def send_post(self, post: 'TGUniversalPost', channel: int) -> Union[telegram.Message, bool]:
        result = False

        if len(post.attachments) == 1:
            result = self._send_photo(post, channel)

        return result

    def _send_photo(self, post: 'TGUniversalPost', channel_id: int) -> Union[telegram.Message, bool]:
        data = dict(
            caption=post.text,
            chat_id=channel_id,
        )

        data['photo'] = post.attachments[0]

        try:
            result = async_to_sync(self.__bot.send_photo)(**data)
            log.debug(result.message_id)
        except telegram.error.TelegramError:
            log.error(f'Send message error', exc_info=True)
            result = False

        return result


class TGUniversalPost(UniversalPost):
    def __init__(self, post_object: TGPost):
        super().__init__()

        # TODO fetch from channel bot
        self.__adapter = TGAdapter()
        self.__post_object = post_object
        self.__post_result: Optional[telegram.Message] = None

    def _prepare(self):
        post = self.__post_object

        attachments = TGAttachment.objects.filter(post=post)
        for attach in attachments.iterator():
            with open(attach.file.path, 'rb') as file:
                self.attachments.append(file.read())

        post.status = post.POSTING
        post.save()

        return True

    def _process_failed(self):
        post = self.__post_object

        post.status = post.FAILED

        post.save(update_fields=['status', ])

        return True

    def _process_success(self):
        post = self.__post_object

        post.status = post.POSTED
        post.posted_dt = timezone.now()
        post.tg_id = self.__post_result.message_id

        post.save(update_fields=['status', 'posted_dt', 'tg_id', ])

        return True

    def _post(self) -> bool:
        channel_tg_id = self.__post_object.channel.tg_id
        self.__post_result = self.__adapter.send_post(self, channel_tg_id)
        return self.__post_result
