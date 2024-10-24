from django.contrib import admin

from tg_core.models.channel import Channel


class ChannelAdmin(admin.ModelAdmin):
    fields = (
        'name',
        'tg_id',
        'is_active',
        'internal_horoscope_sources',
    )

    readonly_fields = ()

    list_filter = (
        'is_active',
    )

    list_display = (
        'name',
        'tg_id',
    )


admin.site.register(Channel, ChannelAdmin)
