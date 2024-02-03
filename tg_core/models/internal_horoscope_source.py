import datetime

from django.db import models

from tg_core.models.base import BaseModel


class InternalHoroscopeSource(BaseModel):
    group = models.ForeignKey('posting.Group', on_delete=models.SET_NULL, null=True)
    repost_time = models.TimeField(default=datetime.time(00, 00), verbose_name='Время постинга из источника')
