import pytest

from posting.models import Group
from posting.tasks import is_horoscopes_conditions


@pytest.fixture(scope='function')
def created_group(create_group, create_horoscope):
    group = create_group(group_type=Group.HOROSCOPES_COMMON)
    create_horoscope(group, zodiac_sign='arises')

    return group


@pytest.mark.freeze_time('2017-05-21 12:00')  # 15:00 msk
def test_suitable_min_time(created_group):
    result = is_horoscopes_conditions(created_group, is_time_to_post=True)
    assert result is True


@pytest.mark.freeze_time('2017-05-21 12:01')  # 15:01 msk
def test_suitable_min_time_boarder(created_group):
    result = is_horoscopes_conditions(created_group, is_time_to_post=True)
    assert result is True


@pytest.mark.freeze_time('2017-05-21 20:59')  # 23:59 msk
def test_suitable_max_time(created_group):
    result = is_horoscopes_conditions(created_group, is_time_to_post=True)
    assert result is True


@pytest.mark.freeze_time('2017-05-21 22:00')  # 00:00 msk
def test_suitable_min_negative_time(created_group):
    result = is_horoscopes_conditions(created_group, is_time_to_post=True)
    assert result is False


@pytest.mark.freeze_time('2017-05-21 11:59')  # 14:59 msk
def test_suitable_max_negative_time(created_group):
    result = is_horoscopes_conditions(created_group, is_time_to_post=True)
    assert result is False


def test_not_suitable_group_time(created_group):
    result = is_horoscopes_conditions(created_group, is_time_to_post=False)

    assert result is False
