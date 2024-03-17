from datetime import timedelta

from django.db import models
from django.utils import timezone

from tg_core.models.base import BaseModel
from tg_core.models.channel import Channel

ALLOWABLE_INACCURACY_IN_SECONDS = 60


class TGPostScheduledNowManager(models.Manager):
    def get_queryset(self):
        now = timezone.now()

        allowable_timedelta = timedelta(seconds=ALLOWABLE_INACCURACY_IN_SECONDS)

        filter_conditions = dict(
            scheduled_dt__range=(now - allowable_timedelta, now + allowable_timedelta),
            status=TGPost.SCHEDULED,
        )

        return super().get_queryset().filter(**filter_conditions)


class TGPost(BaseModel):
    DRAFT = 'draft'
    SCHEDULED = 'scheduled'
    POSTING = 'posting'
    POSTED = 'posted'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    DELETED = 'deleted'

    POST_STATUSES = (
        (DRAFT, 'Draft'),
        (SCHEDULED, 'Scheduled'),
        (POSTING, 'Posting'),
        (POSTED, 'Posted'),
        (FAILED, 'Failed'),
        (CANCELLED, 'Cancelled'),
        (DELETED, 'Deleted'),
    )

    text = models.TextField(max_length=4096, default='', blank=True)
    status = models.CharField(max_length=16, default=DRAFT, choices=POST_STATUSES)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True, blank=False)
    tg_id = models.IntegerField(null=True, blank=True)

    # datetime fields
    scheduled_dt = models.DateTimeField(null=True, blank=True)
    posted_dt = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    scheduled_now = TGPostScheduledNowManager()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'TGPost {self.pk}, {self.status}, scheduled: {self.scheduled_dt}, posted: {self.posted_dt}'
