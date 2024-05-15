import pytest

from posting.models import Group
from posting.tasks import is_it_time_to_post


@pytest.mark.freeze_time('2017-05-21 16:00')
def test_horoscopes_suitable_time(create_group, create_horoscope):
    group = create_group(group_type=Group.HOROSCOPES_COMMON)

    is_time_to_post, last_hour_posts_exist = is_it_time_to_post(group)
    assert is_time_to_post is True


@pytest.mark.freeze_time('2017-05-21 10:00')
def test_horoscopes_bad_time(create_group, create_horoscope):
    group = create_group(group_type=Group.HOROSCOPES_COMMON)

    is_time_to_post, last_hour_posts_exist = is_it_time_to_post(group)
    assert is_time_to_post is False


@pytest.mark.freeze_time('2017-05-21 11:59')
def test_horoscopes_near_min_time(create_group, create_horoscope):
    group = create_group(group_type=Group.HOROSCOPES_COMMON)

    group.posting_minute_base = 59
    group.save()

    is_time_to_post, last_hour_posts_exist = is_it_time_to_post(group)
    assert is_time_to_post is False


@pytest.mark.freeze_time('2017-05-21 12:00')
def test_horoscopes_min_time(create_group, create_horoscope):
    group = create_group(group_type=Group.HOROSCOPES_COMMON)

    is_time_to_post, last_hour_posts_exist = is_it_time_to_post(group)
    assert is_time_to_post is True


@pytest.mark.freeze_time('2017-05-21 20:59')
def test_horoscopes_last_suitable_minute(create_group, create_horoscope):
    group = create_group(group_type=Group.HOROSCOPES_COMMON)

    group.posting_minute_base = 59
    group.save()

    is_time_to_post, last_hour_posts_exist = is_it_time_to_post(group)
    assert is_time_to_post is True


@pytest.mark.freeze_time('2017-05-21 00:00')
def test_horoscopes_day_start(create_group, create_horoscope):
    group = create_group(group_type=Group.HOROSCOPES_COMMON)

    is_time_to_post, last_hour_posts_exist = is_it_time_to_post(group)
    assert is_time_to_post is False
