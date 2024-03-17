import datetime
from datetime import timedelta

import pytest
from django.db.models import QuerySet
from django.utils import timezone

from posting.models import Group
from scraping.models import Horoscope
from services.horoscopes.vars import SIGNS_EN
from tg_core.models import InternalHoroscopeSource, Channel
from tg_core.models.tg_post import TGPost


@pytest.mark.parametrize(
    'wrong_status', [TGPost.DRAFT, TGPost.CANCELLED, TGPost.DELETED, TGPost.POSTING, TGPost.POSTED, TGPost.FAILED])
def test_right_time_wrong_status(wrong_status):
    now = timezone.now()

    TGPost.objects.create(
        scheduled_dt=now,
        status=wrong_status,
    )
    qs = TGPost.scheduled_now.all()

    assert len(qs) == 0


def test_right_status_wrong_time():
    now = timezone.now()

    TGPost.objects.create(
        status=TGPost.SCHEDULED,
        scheduled_dt=now + timedelta(hours=1)
    )

    qs = TGPost.scheduled_now.all()

    assert len(qs) == 0


def test_null_scheduled_dt():
    TGPost.objects.create(
        status=TGPost.SCHEDULED,
    )

    qs = TGPost.scheduled_now.all()

    assert len(qs) == 0


def test_one_post():
    now = timezone.now()

    tg_post = TGPost.objects.create(
        status=TGPost.SCHEDULED,
        scheduled_dt=now + timedelta(seconds=10)
    )

    qs = TGPost.scheduled_now.all()

    assert len(qs) == 1
    assert qs.first().pk == tg_post.pk


def test_multiply_posts():
    now = timezone.now()

    tg_post_1 = TGPost.objects.create(
        status=TGPost.SCHEDULED,
        scheduled_dt=now + timedelta(seconds=29)
    )
    tg_post_2 = TGPost.objects.create(
        status=TGPost.SCHEDULED,
        scheduled_dt=now - timedelta(seconds=29)
    )

    TGPost.objects.create(
        status=TGPost.SCHEDULED,
        scheduled_dt=now - timedelta(seconds=31)
    )

    qs: QuerySet = TGPost.scheduled_now.all()

    assert len(qs) == 2
    assert sorted([tg_post_1.pk, tg_post_2.pk]) == sorted(qs.values_list('pk', flat=True))


def test_horoscope_creation():
    expected_time = datetime.time(10, 33, 00)

    group = Group.objects.create(
        domain_or_id='test',
    )

    horo = Horoscope.objects.create(
        group=group, zodiac_sign=SIGNS_EN[0], text=''
    )

    source = InternalHoroscopeSource.objects.create(
        group=None, repost_time=expected_time
    )

    channel = Channel.objects.create(
        name='@test',
        tg_id=-100000,
    )

    tg_post = TGPost.objects.create_from_source(
        horoscope=horo, channel=channel, source=source
    )

    assert tg_post
    assert tg_post.scheduled_dt.hour == expected_time.hour
    assert tg_post.scheduled_dt.minute == expected_time.minute
    assert tg_post.status == TGPost.SCHEDULED
