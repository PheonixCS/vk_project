from django.db import models

from tg_core.models.base import BaseModel


class TGPost(BaseModel):
    text = models.TextField(max_length=4096, default='', blank=True)
