from posting.models import Group
from scraping.core.horoscopes import save_horoscope_for_main_groups


def test_common(create_group, create_horoscope):
    main = create_group(group_type=Group.HOROSCOPES_MAIN)
    common = create_group(group_type=Group.HOROSCOPES_COMMON)

    horoscope = create_horoscope(group=common, zodiac_sign='arises')
    save_horoscope_for_main_groups(horoscope, 'test', 123, 123)

    actual = len(main.horoscopes.all())

    assert actual == 1


def test_two_groups(create_group, create_horoscope):
    main_one = create_group(group_type=Group.HOROSCOPES_MAIN)
    main_two = create_group(group_type=Group.HOROSCOPES_MAIN)
    common = create_group(group_type=Group.HOROSCOPES_COMMON)

    horoscope = create_horoscope(group=common, zodiac_sign='arises')
    save_horoscope_for_main_groups(horoscope, 'test', 123, 123)

    actual = len(main_one.horoscopes.all()) + len(main_two.horoscopes.all())

    assert actual == 2
