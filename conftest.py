from datetime import timedelta

import pytest
from django.utils import timezone

from posting.models import Group


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(transactional_db):
    pass


@pytest.fixture
def create_group():
    groups = []

    def _create_group(group_id=None, days=7, **kwargs):
        now_time_utc = timezone.now()
        week_ago = now_time_utc - timedelta(days=days)

        group_id = group_id or len(groups) + 1

        group, created = Group.objects.get_or_create(
            domain_or_id='test{}'.format(group_id),
            group_id=group_id,
            sex_last_update_date=week_ago,
            **kwargs
        )
        groups.append(group)
        return group

    yield _create_group
