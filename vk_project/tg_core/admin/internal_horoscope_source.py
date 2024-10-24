from django.contrib import admin

from tg_core.models.internal_horoscope_source import InternalHoroscopeSource


class InternalHoroscopeSourceAdmin(admin.ModelAdmin):
    fields = (
        'group',
        'repost_time',
    )

    readonly_fields = ()

    list_filter = (
        'group',
    )

    list_display = (
        'group',
        'repost_time',
    )


admin.site.register(InternalHoroscopeSource, InternalHoroscopeSourceAdmin)
