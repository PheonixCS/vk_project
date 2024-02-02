from django.db import models

from tg_core.models.base import BaseModel
from tg_core.models.internal_horoscope_source import InternalHoroscopeSource


class Channel(BaseModel):
    name = models.CharField(max_length=256, unique=True)

    is_active = models.BooleanField(default=False)

    internal_horoscope_sources = models.ManyToManyField(InternalHoroscopeSource)

    
