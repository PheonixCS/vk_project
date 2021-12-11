from datetime import timedelta

from django import template
from django.db.models import QuerySet
from django.utils import timezone

register = template.Library()


def count_by_time(value: QuerySet, hours):
    now_time_utc = timezone.now()
    allowed_time_threshold = now_time_utc - timedelta(hours=int(hours))

    return value.filter(add_to_db_date__gte=allowed_time_threshold).count()


register.filter('count_by_time', count_by_time)
