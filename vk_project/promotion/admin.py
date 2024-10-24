from django.contrib import admin

from promotion.models import PromotionTask


class PromotionAdmin(admin.ModelAdmin):
    readonly_fields = ('status', 'external_id')


admin.site.register(PromotionTask, PromotionAdmin)
