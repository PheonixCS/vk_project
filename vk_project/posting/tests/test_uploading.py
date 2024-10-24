from unittest import mock

from services.vk.files import upload_photos
from vk_api import VkApi
import pytest


@mock.patch('vk_api.VkUpload.photo_wall', mock.MagicMock(
    return_value=[{'owner_id': 123, 'id': 1}]
))
def test_upload_one_photo():
    session = VkApi()

    group_id = '123'
    photo = 'test.jpg'

    uploaded = upload_photos(session, photo, group_id)

    assert len(uploaded) == 1


@mock.patch('vk_api.VkUpload.photo_wall', mock.MagicMock(
    return_value=[{'owner_id': 123, 'id': 1}, {'owner_id': 123, 'id': 2}]
))
def test_upload_two_photos():
    session = VkApi()

    group_id = '123'
    photo = ['test.jpg', 'test2.jog']

    uploaded = upload_photos(session, photo, group_id)

    assert len(uploaded) == 2


@mock.patch('vk_api.VkUpload.photo_wall', mock.MagicMock(
    return_value=[{'owner_id': 123, 'id': 1}]
))
def test_result_pattern():
    session = VkApi()

    group_id = '123'
    photo = 'test.jpg'

    uploaded = upload_photos(session, photo, group_id)

    assert uploaded[0] == 'photo123_1'


@mock.patch('vk_api.VkUpload.photo_wall', mock.MagicMock(
    return_value=[{'owner_id': 123, 'id': 1}]
))
def test_raises_exception():
    session = VkApi()

    group_id = '123'
    photos = ['test.jpg', 'test2.jog']

    with pytest.raises(ValueError) as e_info:
        upload_photos(session, photos, group_id)

