from django.contrib import admin

from tg_core.models.tg_attachment import TGAttachment


class TGAttachmentAdmin(admin.ModelAdmin):
    fields = (
        'file',
        'file_type',
        'telegram_file_id',
        'post',
    )

    readonly_fields = (
        'file',
        'file_type',
        'telegram_file_id',
        'post',
    )

    list_filter = (
        'file_type',
    )

    list_display = (
        'pk',
        'file',
        'file_type',
        'telegram_file_id',
        'post',
    )


admin.site.register(TGAttachment, TGAttachmentAdmin)
