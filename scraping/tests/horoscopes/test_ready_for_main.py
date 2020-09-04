from scraping.core.horoscopes import are_horoscopes_for_main_groups_ready
from services.horoscopes.vars import SIGNS_EN
from posting.models import Group


def test_common(create_group, create_horoscope):
    group = create_group(group_type=Group.HOROSCOPES_MAIN)
    for sign in SIGNS_EN:
        create_horoscope(group, zodiac_sign=sign)

    res = are_horoscopes_for_main_groups_ready()

    assert res is True


def test_negative(create_group, create_horoscope):
    group = create_group(group_type=Group.HOROSCOPES_MAIN)

    for sign in SIGNS_EN[:-1]:
        create_horoscope(group, zodiac_sign=sign)

    res = are_horoscopes_for_main_groups_ready()

    assert res is False
