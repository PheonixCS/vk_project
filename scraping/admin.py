from django.contrib import admin
from django.utils.html import format_html

from .models import Donor, Filter


class FilterInLine(admin.StackedInline):
    model = Filter
    extra = 1


class DonorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'vk_url_field',)

    inlines = [FilterInLine]

    def vk_url_field(self, obj):
        return format_html(
            '<a href="https://vk.com/club{}">https://vk.com/club{}</a>'.format(obj.id, obj.id))

    vk_url_field.allow_tags = True
    vk_url_field.short_description = 'Ссылка'


admin.site.register(Donor, DonorAdmin)

