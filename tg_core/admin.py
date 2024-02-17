from django.contrib import admin

from tg_core.models.bot import Bot
from tg_core.models.channel import Channel
from tg_core.models.internal_horoscope_source import InternalHoroscopeSource
from tg_core.models.internal_horoscope_source_link import InternalHoroscopeSourceLink
from tg_core.models.tg_attachment import TGAttachment
from tg_core.models.tg_post import TGPost

# Register your models here.

admin.site.register(Bot)
admin.site.register(Channel)
admin.site.register(InternalHoroscopeSource)
admin.site.register(TGPost)
admin.site.register(TGAttachment)
admin.site.register(InternalHoroscopeSourceLink)
