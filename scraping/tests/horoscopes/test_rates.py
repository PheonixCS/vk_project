import pytest

from posting.core.horoscopes_images import generate_rates
from posting.models import Group
from scraping.models import Horoscope


@pytest.fixture(scope='function')
def generate_horoscope(create_group, create_horoscope) -> Horoscope:
    group = create_group(group_type=Group.HOROSCOPES_MAIN)
    horo: Horoscope = create_horoscope(group_id=group.pk, zodiac_sign='arises')
    return horo


@pytest.mark.usefixtures('generate_horoscope')
def test_creation(generate_horoscope):
    assert 5555 <= generate_horoscope.rates <= 9999


@pytest.mark.usefixtures('generate_horoscope')
def test_rates_generation(generate_horoscope):
    rates, _ = generate_rates(generate_horoscope.rates)

    assert all([5 <= int(rate) <= 9 for rate in rates.values()]), f'{rates}, {generate_horoscope.rates}'
