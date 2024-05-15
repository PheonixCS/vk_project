import pytest

from posting.models import Group
from posting.tasks import is_horoscopes_conditions


@pytest.fixture(scope='function')
def preconditions(create_group, create_horoscope):
    group = create_group(group_type=Group.HOROSCOPES_COMMON)
    create_horoscope(group, zodiac_sign='arises')

    return group


def test_positive(preconditions):
    result = is_horoscopes_conditions(preconditions, is_time_to_post=True)

    assert result is True


def test_negative(preconditions):
    result = is_horoscopes_conditions(preconditions, is_time_to_post=False)

    assert result is False
