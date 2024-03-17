from datetime import timedelta

import pytest
from django.db.models import QuerySet
from django.utils import timezone

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
        scheduled_dt=now + timedelta(seconds=59)
    )
    tg_post_2 = TGPost.objects.create(
        status=TGPost.SCHEDULED,
        scheduled_dt=now - timedelta(seconds=59)
    )

    TGPost.objects.create(
        status=TGPost.SCHEDULED,
        scheduled_dt=now - timedelta(seconds=61)
    )

    qs: QuerySet = TGPost.scheduled_now.all()

    assert len(qs) == 2
    assert sorted([tg_post_1.pk, tg_post_2.pk]) == sorted(qs.values_list('pk', flat=True))
