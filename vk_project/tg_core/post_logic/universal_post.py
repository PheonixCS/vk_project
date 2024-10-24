# Universal post interface
from abc import ABC, abstractmethod

from django.utils import timezone


class UniversalPost(ABC):
    NEW = 'new'
    PREPARED = 'prepared'
    FAILED = 'failed'
    SENT = 'sent'

    def __init__(self):
        self.text = ''
        self.attachments = []

        self.created_dt = timezone.now()
        self.posted_dt = None

        self.__status = self.NEW

    @property
    def status(self):
        return self.__status

    @abstractmethod
    def _prepare(self) -> bool:
        pass

    @abstractmethod
    def _post_failed_hook(self) -> None:
        pass

    @abstractmethod
    def _post_succeeded_hook(self) -> None:
        pass

    @abstractmethod
    def _post(self) -> bool:
        pass

    def prepare(self):
        prepare_result = self._prepare()
        if prepare_result:
            self.__status = self.PREPARED
        else:
            self.__status = self.FAILED

    def post(self) -> str:
        """
        Post prepared post to target.

        target may be tg channel, user, or anything else.
        """
        if self.status == self.PREPARED:
            post_result = self._post()
            if post_result:
                self._post_succeeded_hook()
                self.__status = self.SENT
            else:
                self._post_failed_hook()
                self.__status = self.FAILED
        else:
            raise Exception(f'{self} is not prepared for posting yet!')

        return self.status


class UniversalAttachment:
    def __init__(self):
        pass
