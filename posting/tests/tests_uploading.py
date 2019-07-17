from django.test import TestCase
from unittest import mock

from services.vk.files import upload_photos
from vk_api import VkApi


class UploadPhotoTest(TestCase):
    @mock.patch('vk_api.VkUpload.photo_wall', mock.MagicMock(
        return_value=[{'owner_id': 123, 'id': 1}]
    ))
    def test_upload_one_photo(self):
        session = VkApi()
        group_id = '123'

        photo = 'test.jpg'

        uploaded = upload_photos(session, photo, group_id)

        self.assertIsInstance(uploaded, str)

    @mock.patch('vk_api.VkUpload.photo_wall', mock.MagicMock(
        return_value=[{'owner_id': 123, 'id': 1}, {'owner_id': 123, 'id': 2}]
    ))
    def test_upload_two_photos(self):
        session = VkApi()
        group_id = '123'

        photo = ['test.jpg', 'test2.jog']

        uploaded = upload_photos(session, photo, group_id)

        self.assertIsInstance(uploaded, list)

    @mock.patch('vk_api.VkUpload.photo_wall', mock.MagicMock(
        return_value=[{'owner_id': 123, 'id': 1}]
    ))
    def test_result_pattern(self):
        session = VkApi()
        group_id = '123'

        photo = 'test.jpg'

        uploaded = upload_photos(session, photo, group_id)

        self.assertEqual(uploaded, 'photo123_1')
