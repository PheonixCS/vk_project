from django.contrib import admin
from django.utils.html import format_html

from .models import Donor, Filter


class FilterInLine(admin.StackedInline):
    model = Filter
    extra = 1


class DonorAdmin(admin.ModelAdmin):
    exclude = ('url',)
    readonly_fields = ('vk_url_field',)
    list_display = ('id', 'vk_url_field',)

    inlines = [FilterInLine]

    def vk_url_field(self, obj):
        if obj.name:
            return format_html(f'<a href="{obj.url}">{obj.name}</a>')
        else:
            return format_html(f'<a href="{obj.url}">{obj.url}</a>')

    vk_url_field.allow_tags = True
    vk_url_field.short_description = 'Ссылка'


admin.site.register(Donor, DonorAdmin)

