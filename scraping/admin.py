from django.contrib import admin
from django.utils.html import format_html

from .models import Donor, Filter, Record


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
            return format_html(f'<a href="{obj.url}" target="_blank" rel="noopener noreferrer">{obj.name}</a>')
        else:
            return format_html(f'<a href="{obj.url}" target="_blank" rel="noopener noreferrer">{obj.url}</a>')

    vk_url_field.allow_tags = True
    vk_url_field.short_description = 'Ссылка'


class RecordAdmin(admin.ModelAdmin):
    list_display = [
        '__str__',
        'donor',
        'group',
        'post_in_donor_url_field',
        'post_in_group_url_field',
        'post_in_group_date'
    ]
    search_fields = [
        'group_url'
    ]
    list_filter = [
        'group'
    ]
    ordering = [
        'post_in_group_date'
    ]

    def post_in_donor_url_field(self, obj):
        return format_html(f'<a href="{obj.donor_url}" target="_blank" rel="noopener noreferrer">{obj.donor_url}</a>')

    def post_in_group_url_field(self, obj):
        return format_html(f'<a href="{obj.group_url}" target="_blank" rel="noopener noreferrer">{obj.group_url}</a>')

    post_in_donor_url_field.allow_tags = True
    post_in_donor_url_field.short_description = 'Пост в источнике'
    post_in_group_url_field.allow_tags = True
    post_in_group_url_field.short_description = 'Пост в сообществе'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            self.readonly_fields = [field.name for field in obj.__class__._meta.fields]
        return self.readonly_fields

    def get_queryset(self, request):
        qs = super(RecordAdmin, self).get_queryset(request)
        return qs.filter(post_in_group_date__isnull=False)


admin.site.register(Donor, DonorAdmin)
admin.site.register(Record, RecordAdmin)
