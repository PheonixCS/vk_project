from django.test import TestCase
from constance.test import override_config

from posting.models import Group
from posting.core.poster import get_groups_to_update_sex_statistics
from django.utils import timezone
from datetime import timedelta


class SexStatisticsTests(TestCase):
    def setUp(self):
        self.group_ids = [1, 2, 3, 4, 5]

    def create_groups(self, days=7):
        for group_id in self.group_ids:
            now_time_utc = timezone.now()
            week_ago = now_time_utc - timedelta(days=days)
            Group.objects.get_or_create(domain_or_id='test{}'.format(group_id),
                                        group_id=group_id,
                                        sex_last_update_date=week_ago)

    @override_config(EXCLUDE_GROUPS_FROM_SEX_STATISTICS_UPDATE='[]')
    def test_mistake_in_config(self):
        self.create_groups()
        groups = get_groups_to_update_sex_statistics()

        self.assertEqual(len(groups), len(self.group_ids))

    @override_config(EXCLUDE_GROUPS_FROM_SEX_STATISTICS_UPDATE='')
    def test_empty_config(self):
        self.create_groups()
        groups = get_groups_to_update_sex_statistics()

        self.assertEqual(len(groups), len(self.group_ids))

    @override_config(EXCLUDE_GROUPS_FROM_SEX_STATISTICS_UPDATE='[1,2]')
    def test_default(self):
        self.create_groups()
        groups = get_groups_to_update_sex_statistics()

        self.assertEqual(len(groups), 3)

    def test_time_threshold(self):
        self.create_groups(days=5)
        groups = get_groups_to_update_sex_statistics()

        self.assertEqual(len(groups), 0)
