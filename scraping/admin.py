from django.contrib import admin
from django.utils.html import format_html

from .models import Donor, Filter, Record, ScrapingHistory


class FilterInLine(admin.StackedInline):
    model = Filter
    extra = 1


class DonorAdmin(admin.ModelAdmin):
    exclude = ('url',)
    readonly_fields = ('vk_url_field', 'average_views_number')
    list_display = ('id', 'vk_url_field',)

    inlines = [FilterInLine]

    def vk_url_field(self, obj):
        if obj.name:
            return format_html(f'<a href="{obj.url}" target="_blank" rel="noopener noreferrer">{obj.name}</a>')
        else:
            return format_html(f'<a href="{obj.url}" target="_blank" rel="noopener noreferrer">{obj.url}</a>')

    vk_url_field.allow_tags = True
    vk_url_field.short_description = 'Ссылка'


class IsPostedFilter(admin.SimpleListFilter):
    title = 'is_posted'
    parameter_name = 'is_posted'

    def lookups(self, request, model_admin):
        return (
            ('Yes', 'Yes'),
            ('No', 'No'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'Yes':
            return queryset.filter(post_in_group_date__isnull=False)
        elif value == 'No':
            return queryset.exclude(post_in_group_date__isnull=False)
        return queryset


class RecordAdmin(admin.ModelAdmin):
    exclude = [
        'females_count',
        'males_count',
        'males_females_ratio',
        'unknown_count'
    ]
    list_display = [
        '__str__',
        'donor',
        'group',
        'post_in_donor_url_field',
        'post_in_group_url_field',
        'post_in_group_date',
        'post_audience_ratio',
        'group_audience_ratio',
        'is_posted'
    ]
    search_fields = [
        'group_url'
    ]
    list_filter = [
        'group', IsPostedFilter
    ]
    ordering = [
        '-post_in_group_date'
    ]

    def post_in_donor_url_field(self, obj):
        return format_html(f'<a href="{obj.donor_url}" target="_blank" rel="noopener noreferrer">{obj.donor_url}</a>')

    def post_in_group_url_field(self, obj):
        if obj.group_url:
            return format_html(f'<a href="{obj.group_url}" target="_blank" rel="noopener noreferrer">{obj.group_url}</a>')
        else:
            return ''

    def post_audience_ratio(self, obj):
        if obj.males_count and obj.females_count:
            return '{}% М {}% Ж'.format(round(obj.males_count / (obj.males_count + obj.females_count) * 100),
                                        round(obj.females_count / (obj.males_count + obj.females_count) * 100))

    def group_audience_ratio(self, obj):
        try:
            males = obj.group.male_weekly_average_count
            females = obj.group.female_weekly_average_count
        except AttributeError:
            males, females = None, None
        if males and females:
            return '{}% М {}% Ж'.format(round(males / (males + females) * 100),
                                        round(females / (males + females) * 100))
        else:
            return 'None'

    post_in_donor_url_field.allow_tags = True
    post_in_donor_url_field.short_description = 'Пост в источнике'
    post_in_group_url_field.allow_tags = True
    post_in_group_url_field.short_description = 'Пост в сообществе'
    post_audience_ratio.short_description = 'Лайкнувшие пост в источнике'
    group_audience_ratio.short_description = 'Аудитория в сообществе'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            self.readonly_fields = [field.name for field in obj.__class__._meta.fields]
        return self.readonly_fields

    # def get_queryset(self, request):
    #     qs = super(RecordAdmin, self).get_queryset(request)
    #     return qs.filter(post_in_group_date__isnull=False)

    def is_posted(self, obj):
        return obj.post_in_group_date is None





class ScrapingHistoryAdmin(admin.ModelAdmin):
    ordering = ['-created_at']
    list_filter = ('filter_name', 'group')
    search_fields = ['group', 'filter_name']

    readonly_fields = ('created_at', 'group', 'filter_name', 'filtered_number')
    list_display = ('created_at', 'group', 'filter_name', 'filtered_number')


admin.site.register(Donor, DonorAdmin)
admin.site.register(Record, RecordAdmin)
admin.site.register(ScrapingHistory, ScrapingHistoryAdmin)
