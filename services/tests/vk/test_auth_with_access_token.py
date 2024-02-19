from unittest import mock

import vk_api

from posting.models import User
from services.vk.auth_with_access_token import generate_url_for_access_token_generation, \
    create_vk_session_with_access_token


def create_test_user(**kwargs):
    return User.objects.create(
        login='Test',
        password='pass',
        **kwargs
    )


@mock.patch('services.vk.auth_with_access_token.vk_api.VkApi')
def test_session_creation(api_mock: mock.MagicMock):
    expected_token = 'test_token'
    expected_app_id = 123
    expected_api_ver = '5.131'
    expected_scope = 'wall,offline,stats'

    expected_data = dict(
        access_token=expected_token,
        applicatoin_id=expected_app_id,
        api_version=expected_api_ver,
        scope=expected_scope,
    )

    api_mock_class = mock.create_autospec(vk_api.VkApi)
    api_mock.return_value = api_mock_class

    user = create_test_user(app_id=expected_app_id, access_token=expected_token)

    result = create_vk_session_with_access_token(user)

    assert api_mock_class.assert_called_once_with(**expected_data)
    assert result is api_mock_class


def test_url_creation():
    expected_id = 123
    expected_scopes = 'wall,offline,stats'
    expected_url = f'https://oauth.vk.com/authorize?client_id={expected_id}&redirect_uri=https://oauth.vk.com/blank.html&display=mobile&scope={expected_scopes}&response_type=token&revoke=1'

    user = create_test_user(app_id=expected_id)

    actual_url = generate_url_for_access_token_generation(user)

    assert actual_url == expected_url
