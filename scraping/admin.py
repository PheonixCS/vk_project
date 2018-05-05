from django.contrib import admin

from .models import Donor, Filter, Record

admin.site.register(Donor)
admin.site.register(Filter)
admin.site.register(Record)

