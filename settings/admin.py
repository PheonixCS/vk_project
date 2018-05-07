from django.contrib import admin

from .models import Setting


class SettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'key_type', 'value', 'description')


admin.site.register(Setting, SettingAdmin)