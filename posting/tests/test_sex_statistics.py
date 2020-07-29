from posting.models import Group
from posting.core.poster import get_groups_to_update_sex_statistics


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
