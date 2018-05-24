from django.contrib import admin

from .models import User, ServiceToken, Group


class MembershipInline(admin.TabularInline):
    model = Group.donors.through
    extra = 1


class DonorAdmin(admin.ModelAdmin):
    inlines = [
        MembershipInline,
    ]


class GroupAdmin(admin.ModelAdmin):
    inlines = [
        MembershipInline,
    ]
    exclude = ('group_id', 'donors')


admin.site.register(User)
admin.site.register(ServiceToken)
admin.site.register(Group, GroupAdmin)
