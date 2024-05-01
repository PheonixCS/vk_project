from posting.models import Group
from scraping.models import Horoscope


def test_creation(create_group, create_horoscope):
    group = create_group(group_type=Group.HOROSCOPES_MAIN)
    horo: Horoscope = create_horoscope(group_id=group.pk, zodiac_sign='arises')
    assert 5555 <= horo.rates <= 9999
