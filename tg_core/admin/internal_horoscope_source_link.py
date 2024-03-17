from django.contrib import admin

from tg_core.models import InternalHoroscopeSourceLink


class InternalHoroscopeSourceLinkAdmin(admin.ModelAdmin):
    fields = (
        'source_post',
        'target_post',
        'link',
    )

    readonly_fields = (
        'source_post',
        'target_post',
        'link',
    )

    list_filter = ()

    list_display = (
        'pk',
        'source_post',
        'target_post',
        'link',
    )


admin.site.register(InternalHoroscopeSourceLink, InternalHoroscopeSourceLinkAdmin)
