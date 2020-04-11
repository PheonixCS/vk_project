import logging

from posting.models import Group
from services.vk.core import create_vk_session_using_login_password

log = logging.getLogger('posting.vk_record')


class VkRecord:
    def __init__(self, group: Group):
        self.group = group

        self.post_response = None

        self.__session = None
        self.__api = None
        self.__attachments = []
        self.__record_text = ''

    def prepare(self):
        self.__prepare_api()

    def post(self):
        default_data = {
            'owner_id': f'-{self.group.group_id}',
            'from_group': 1
        }

        data = dict()
        data.update(default_data)

        if self.__record_text:
            data.update({'message': self.__record_text})

        if self.__attachments:
            data.update({'attachments': self.__attachments})
        elif 'message' not in data.keys():
            data.update({'message': ''})

        self.post_response = self.__api.wall.post(**data)

    def __prepare_session(self):
        if not self.__session:
            login = self.group.user.login
            password = self.group.user.password
            app_id = self.group.user.app_id

            self.__session = create_vk_session_using_login_password(login, password, app_id)

    def __prepare_api(self):
        if not self.__api:
            self.__prepare_session()
            self.__api = self.__session.get_api()


class CommonVkRecord(VkRecord):
    def __init__(self, group, record):
        self.__record_obj = record

        super(CommonVkRecord, self).__init__(group)

    def __prepare_text(self):
        pass

    def __prepare_attachments(self):
        pass
