from django.contrib import admin
from django.utils.html import format_html

from .models import User, ServiceToken, Group


class MembershipInline(admin.TabularInline):
    model = Group.donors.through
    extra = 1


class DonorAdmin(admin.ModelAdmin):
    inlines = [
        MembershipInline,
    ]


class GroupAdmin(admin.ModelAdmin):
    exclude = (
        'url',
        'group_id',
        'donors',
        'members_count'
        'members_growth',
        'number_of_posts_yesterday',
        'number_of_ad_posts_yesterday',
        'statistic_url',
        'statistics_last_update_date'
    )
    readonly_fields = (
        'vk_url_field',
        'members_count',
        'members_growth',
        'number_of_posts_yesterday',
        'number_of_ad_posts_yesterday',
    )
    list_display = (
        'domain_or_id',
        'vk_url_field',
        'members_count',
        'members_growth',
        'number_of_posts_yesterday',
        'number_of_ad_posts_yesterday',
        'statistic_url',
    )

    inlines = [
        MembershipInline,
    ]

    def vk_url_field(self, obj):
        if obj.name:
            return format_html(f'<a href="{obj.url}" target="_blank" rel="noopener noreferrer">{obj.name}</a>')
        else:
            return format_html(f'<a href="{obj.url}" target="_blank" rel="noopener noreferrer">{obj.url}</a>')

    def vk_statistics_url_field(self, obj):
        return format_html(f'<a href="{obj.statistic_url}" target="_blank" rel="noopener noreferrer">{obj.statistic_url}</a>')

    vk_url_field.allow_tags = True
    vk_statistics_url_field.allow_tags = True
    vk_url_field.short_description = 'Ссылка'
    vk_statistics_url_field.short_description = 'Статистика'


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
