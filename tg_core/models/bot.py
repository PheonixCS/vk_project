from django.db import models

from tg_core.models.base import BaseModel


class Bot(BaseModel):
    name = models.CharField(max_length=64)
    token = models.CharField(max_length=64)
