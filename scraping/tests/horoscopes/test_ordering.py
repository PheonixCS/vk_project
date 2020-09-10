from scraping.models import Horoscope
from services.horoscopes.vars import SIGNS_EN
from posting.models import Group


def test_ordering(create_group, create_horoscope):
    group = create_group(group_type=Group.HOROSCOPES_MAIN)
    for sign in SIGNS_EN:
        create_horoscope(group, zodiac_sign=sign)

    actual_list = list(Horoscope.objects.all().values_list('zodiac_sign', flat=True))

    assert actual_list == list(SIGNS_EN[::-1])
