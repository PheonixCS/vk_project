from django.db import models

from tg_core.models.base import BaseModel
from tg_core.models.channel import Channel


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
    tg_id = models.IntegerField()

    # datetime fields
    scheduled_dt = models.DateTimeField(null=True, blank=True)
    posted_dt = models.DateTimeField(null=True, blank=True)
