from django.contrib import admin

from tg_core.models.text_template import TextTemplate


class TextTemplateAdmin(admin.ModelAdmin):
    fields = (
        'slug',
        'template',
    )

    readonly_fields = ()

    list_filter = ()

    list_display = (
        'slug',
    )

    search_fields = (
        'slug',
        'template',
    )


admin.site.register(TextTemplate, TextTemplateAdmin)
