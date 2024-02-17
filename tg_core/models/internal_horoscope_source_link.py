from django.db import models

from scraping.models import Horoscope
from tg_core.models.base import BaseModel
from tg_core.models.internal_horoscope_source import InternalHoroscopeSource
from tg_core.models.tg_post import TGPost


class InternalHoroscopeSourceLink(BaseModel):
    source_post = models.ForeignKey(Horoscope, on_delete=models.SET_NULL, null=True)
    target_post = models.ForeignKey(TGPost, on_delete=models.SET_NULL, null=True)
    link = models.ForeignKey(InternalHoroscopeSource, on_delete=models.SET_NULL, null=True)
