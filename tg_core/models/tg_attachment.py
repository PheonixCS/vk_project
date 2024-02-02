import os

from django.db import models
from django.dispatch import receiver

from tg_core.models.base import BaseModel
from tg_core.models.tg_post import TGPost


class TGAttachment(BaseModel):
    IMAGE = 'image'

    TYPES = (
        (IMAGE, 'Image'),
    )

    file = models.FileField(upload_to='tg_attachments/')
    file_type = models.CharField(max_length=64, choices=TYPES, default=IMAGE)
    telegram_file_id = models.CharField(max_length=256, default='', blank=True)

    post = models.ForeignKey(TGPost, on_delete=models.CASCADE, null=True, blank=True)


@receiver(models.signals.post_delete, sender=TGAttachment)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
