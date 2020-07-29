from posting.models import Group


class TestPostingIntervals:
    def test_defaults(self, create_group):
        create_group()

        expected = [
            (0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0),
            (7, 0), (8, 0), (9, 0), (10, 0), (11, 0), (12, 0), (13, 0),
            (14, 0), (15, 0), (16, 0), (17, 0), (18, 0), (19, 0), (20, 0),
            (21, 0), (22, 0), (23, 0),
        ]

        group = Group.objects.first()
        actual = group.return_posting_time_list()

        assert expected == actual

    def test_minutes(self, create_group):
        create_group(posting_minute_base=1)

        expected = [
            (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1),
            (7, 1), (8, 1), (9, 1), (10, 1), (11, 1), (12, 1), (13, 1),
            (14, 1), (15, 1), (16, 1), (17, 1), (18, 1), (19, 1), (20, 1),
            (21, 1), (22, 1), (23, 1),
        ]

        group = Group.objects.first()
        actual = group.return_posting_time_list()

        assert expected == actual

    def test_double_interval(self, create_group):
        create_group(posting_minute_base=0, posting_interval=120)

        expected = [
            (0, 0), (2, 0), (4, 0), (6, 0),
            (8, 0), (10, 0), (12, 0),
            (14, 0), (16, 0), (18, 0), (20, 0),
            (22, 0),
        ]

        group = Group.objects.first()
        actual = group.return_posting_time_list()

        assert expected == actual

    def test_one_and_a_half(self, create_group):
        create_group(posting_minute_base=0, posting_interval=90)

        expected = [
            (0, 0), (1, 30), (3, 0), (4, 30),
            (6, 0), (7, 30), (9, 0), (10, 30),
            (12, 0), (13, 30), (15, 0), (16, 30), (18, 0), (19, 30), (21, 0),
            (22, 30),
        ]

        group = Group.objects.first()
        actual = group.return_posting_time_list()

        assert expected == actual
