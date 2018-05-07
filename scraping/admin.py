from django.contrib import admin

from .models import Donor, Filter, Record


class FilterInLine(admin.StackedInline):
    model = Filter
    extra = 1


class DonorAdmin(admin.ModelAdmin):
    inlines = [FilterInLine]


admin.site.register(Donor, DonorAdmin)

