from django.contrib import admin

from .models import User, Group


class GroupAdmin(admin.ModelAdmin):
    exclude = ('group_id',)


admin.site.register(User)
admin.site.register(Group, GroupAdmin)
