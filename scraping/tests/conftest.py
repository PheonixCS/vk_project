from datetime import timedelta

import pytest
from django.utils import timezone

from scraping.models import Horoscope


@pytest.fixture
def create_horoscope():
    records = []

    def _create_horoscope(group=None, **kwargs):
        now_time_utc = timezone.now()
        fake_posting_time = now_time_utc - timedelta(minutes=30)

        horoscope = Horoscope.objects.create(
            group=group,
            post_in_group_date=fake_posting_time,
            **kwargs
        )
        records.append(horoscope)
        return horoscope

    yield _create_horoscope
