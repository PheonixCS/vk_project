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
    exclude = ('url', 'group_id', 'donors')
    readonly_fields = ('vk_url_field',)
    list_display = ('domain_or_id', 'vk_url_field',)

    inlines = [
        MembershipInline,
    ]

    def vk_url_field(self, obj):
        if obj.name:
            return format_html('<a href="{}">{}</a>'.format(obj.url, obj.name))
        else:
            return format_html('<a href="{}">{}</a>'.format(obj.url, obj.url))

    vk_url_field.allow_tags = True
    vk_url_field.short_description = 'Ссылка'


class UserAdmin(admin.ModelAdmin):
    exclude = ('url',)
    readonly_fields = ('vk_url_field',)
    list_display = ('login', 'vk_url_field',)

    def vk_url_field(self, obj):
        if obj.url:
            if obj.initials:
                return format_html('<a href="{}">{}</a>'.format(obj.url, obj.initials))
            else:
                return format_html('<a href="{}">{}</a>'.format(obj.url, obj.url))
        else:
            return obj.initials

    vk_url_field.allow_tags = True
    vk_url_field.short_description = 'Ссылка'


admin.site.register(User, UserAdmin)
admin.site.register(ServiceToken)
admin.site.register(Group, GroupAdmin)
