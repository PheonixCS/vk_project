from django.db import models


class PromotionTask(models.Model):
    NEW = 'new'
    SENT = 'sent'
    FAILED = 'failed'
    DONE = 'done'

    statuses = (
        (NEW, 'new'),
        (SENT, 'sent'),
        (FAILED, 'failed'),
        (DONE, 'done'),
    )

    external_id = models.IntegerField()
    status = models.CharField(choices=statuses, default=NEW, max_length=32)
    status_result = models.TextField(default='')

    created_dt = models.DateTimeField(auto_now_add=True)
    updated_dt = models.DateTimeField(auto_now=True)
