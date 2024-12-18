from django.contrib import admin

from tg_core.models import TGAttachment
from tg_core.models.tg_post import TGPost


class TGAttachmentInline(admin.TabularInline):
    model = TGAttachment
    extra = 0

    def has_add_permission(self, request, obj):
        return False


class TGPostAdmin(admin.ModelAdmin):
    fields = (
        'text',
        'status',
        'channel',
        'tg_id',
        'scheduled_dt',
        'posted_dt',
    )

    readonly_fields = (
        'channel',
        'tg_id',
        'posted_dt',
    )

    list_filter = (
        'status',
        'channel',
    )

    list_display = (
        'pk',
        'status',
        'channel',
        'scheduled_dt',
        'posted_dt',
    )

    inlines = (
        TGAttachmentInline,
    )


admin.site.register(TGPost, TGPostAdmin)
