from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.db.models import Sum, TextField
from django.forms import Textarea
from django.utils.html import format_html

from .models import User, ServiceToken, Group, AdditionalText


class MembershipInline(admin.TabularInline):
    model = Group.donors.through
    extra = 1


class DonorAdmin(admin.ModelAdmin):
    inlines = [
        MembershipInline,
    ]


class AdditionalTextInline(admin.TabularInline):
    model = AdditionalText
    extra = 1

    formfield_overrides = {
        TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 60})},
    }


class GroupChangeList(ChangeList):
    fields_to_total = ['members_count', 'members_growth', 'number_of_posts_yesterday', 'number_of_ad_posts_yesterday']

    def get_total_values(self, queryset):
        total = Group()
        for field in self.fields_to_total:
            setattr(total, field, queryset.aggregate(Sum(field)).get(f'{field}__sum'))
        return total

    def get_results(self, request):
        super(GroupChangeList, self).get_results(request)
        total = self.get_total_values(self.queryset)
        # do not delete it, len() is used for evaluate the queryset
        len(self.result_list)
        self.result_list._result_cache.append(total)


class GroupAdmin(admin.ModelAdmin):
    exclude = (
        'url',
        'group_id',
        'donors',
        'statistic_url',
        'statistics_last_update_date'
    )
    readonly_fields = (
        'vk_url_field',
        'vk_statistics_url_field',
        'members_count',
        'members_growth',
        'number_of_posts_yesterday',
        'number_of_ad_posts_yesterday',
        'group_audience'
    )
    list_display = (
        'domain_or_id',
        'vk_url_field',
        'members_count',
        'members_growth',
        'number_of_posts_yesterday',
        'number_of_ad_posts_yesterday',
        'vk_statistics_url_field',
        'group_audience',
    )
    fieldsets = (
        (None, {
            'fields': ('domain_or_id', 'name', 'is_posting_active', 'is_horoscopes', 'is_pin_enabled', 'posting_time',
                       'user', 'callback_api_token')
        }),
        ('Параметры уникализации', {
            'fields': ('is_text_delete_enabled', 'is_delete_audio_enabled', 'is_text_filling_enabled',
                       'is_image_mirror_enabled', 'is_changing_image_to_square_enabled', 'RGB_image_tone',
                       'is_photos_shuffle_enabled', 'is_audios_shuffle_enabled', 'is_merge_images_enabled',
                       'is_replace_russian_with_english', 'is_additional_text_enabled')
        }),
        ('Статистика', {
            'classes': ('collapse',),
            'fields': ('vk_statistics_url_field', 'members_count', 'members_growth', 'number_of_posts_yesterday',
                       'number_of_ad_posts_yesterday', 'group_audience')
        })
    )

    inlines = [
        MembershipInline, AdditionalTextInline,
    ]

    def vk_url_field(self, obj):
        if obj.name:
            return format_html(f'<a href="{obj.url}" target="_blank" rel="noopener noreferrer">{obj.name}</a>')
        else:
            return format_html(f'<a href="{obj.url}" target="_blank" rel="noopener noreferrer">{obj.url}</a>')

    def vk_statistics_url_field(self, obj):
        return format_html(
            f'<a href="{obj.statistic_url}" target="_blank" rel="noopener noreferrer">{obj.statistic_url}</a>')

    def group_audience(self, obj):
        males = obj.male_weekly_average_count
        females = obj.female_weekly_average_count
        if males and females:
            return '{}% М {}% Ж'.format(round(males / (males + females) * 100),
                                        round(females / (males + females) * 100))

    vk_url_field.allow_tags = True
    vk_statistics_url_field.allow_tags = True

    vk_url_field.short_description = 'Ссылка'
    vk_statistics_url_field.short_description = 'Статистика'
    group_audience.short_description = 'Аудитория'

    def get_changelist(self, request, **kwargs):
        return GroupChangeList


class UserAdmin(admin.ModelAdmin):
    exclude = ('url',)
    readonly_fields = ('vk_url_field',)
    list_display = ('login', 'vk_url_field',)

    def vk_url_field(self, obj):
        if obj.url:
            if obj.initials:
                return format_html(f'<a href="{obj.url}" target="_blank" rel="noopener noreferrer">{obj.initials}</a>')
            else:
                return format_html(f'<a href="{obj.url}" target="_blank" rel="noopener noreferrer">{obj.url}</a>')
        else:
            return obj.initials

    vk_url_field.allow_tags = True
    vk_url_field.short_description = 'Ссылка'


admin.site.register(User, UserAdmin)
admin.site.register(ServiceToken)
admin.site.register(Group, GroupAdmin)
