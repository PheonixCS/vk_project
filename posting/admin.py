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
    list_display = ('domain_or_id', 'name', 'vk_url_field',)

    inlines = [
        MembershipInline,
    ]
    exclude = ('group_id', 'donors')

    def vk_url_field(self, obj):
        return format_html('<a href="https://vk.com/club{}">https://vk.com/club{}</a>'.format(obj.name, obj.name))

    vk_url_field.allow_tags = True
    vk_url_field.short_description = 'Ссылка'


class UserAdmin(admin.ModelAdmin):
    list_display = ('login', 'initials', 'vk_url_field',)

    def vk_url_field(self, obj):
        return format_html(
            '<a href="https://vk.com/{}">https://vk.com/{}</a>'.format(obj.domain_or_id, obj.domain_or_id))

    vk_url_field.allow_tags = True
    vk_url_field.short_description = 'Ссылка'


admin.site.register(User, UserAdmin)
admin.site.register(ServiceToken)
admin.site.register(Group, GroupAdmin)
