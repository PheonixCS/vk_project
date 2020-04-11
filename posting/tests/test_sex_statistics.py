from posting.models import Group
from posting.core.poster import get_groups_to_update_sex_statistics
from django.utils import timezone
from datetime import timedelta
import pytest


@pytest.fixture
def create_group():
    groups = []

    def _create_group(group_id=None, days=7, **kwargs):
        now_time_utc = timezone.now()
        week_ago = now_time_utc - timedelta(days=days)

        group_id = group_id or len(groups) + 1

        group = Group.objects.get_or_create(
            domain_or_id='test{}'.format(group_id),
            group_id=group_id,
            sex_last_update_date=week_ago,
            **kwargs
        )
        groups.append(group)
        return group

    yield _create_group


class TestSexStatistics:
    def test_default(self, create_group):
        create_group()
        create_group()
        create_group()

        groups = get_groups_to_update_sex_statistics()

        assert len(groups) == 3

    def test_time_threshold(self, create_group):
        create_group(days=3)
        create_group(days=4)

        groups = get_groups_to_update_sex_statistics()

        assert len(groups) == 0

    def test_wrong_group_type(self, create_group):
        create_group(group_type=Group.MUSIC_COMMON)
        create_group()
        create_group()

        groups = get_groups_to_update_sex_statistics()

        assert len(groups) == 2

    def test_excluded_groups(self, create_group):
        create_group(group_id=1)
        create_group(group_id=2)
        create_group(group_id=3)

        groups = get_groups_to_update_sex_statistics(exclude_groups=[1, 2])

        assert len(groups) == 1
        assert groups.first().group_id == 3
