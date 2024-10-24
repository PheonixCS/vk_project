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

    def test_custom_time(self, create_group):
        create_group()

        expected = sorted([
            (0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0),
            (0, 15), (1, 15), (2, 15), (3, 15), (4, 15), (5, 15), (6, 15),
            (0, 30), (1, 30), (2, 30), (3, 30), (4, 30), (5, 30), (6, 30),
            (0, 45), (1, 45), (2, 45), (3, 45), (4, 45), (5, 45), (6, 45),
            (7, 0), (8, 0), (9, 0), (10, 0), (11, 0), (12, 0), (13, 0),
            (7, 15), (8, 15), (9, 15), (10, 15), (11, 15), (12, 15), (13, 15),
            (7, 30), (8, 30), (9, 30), (10, 30), (11, 30), (12, 30), (13, 30),
            (7, 45), (8, 45), (9, 45), (10, 45), (11, 45), (12, 45), (13, 45),
            (14, 0), (15, 0), (16, 0), (17, 0), (18, 0), (19, 0), (20, 0),
            (14, 15), (15, 15), (16, 15), (17, 15), (18, 15), (19, 15), (20, 15),
            (14, 30), (15, 30), (16, 30), (17, 30), (18, 30), (19, 30), (20, 30),
            (14, 45), (15, 45), (16, 45), (17, 45), (18, 45), (19, 45), (20, 45),
            (21, 0), (22, 0), (23, 0),
            (21, 15), (22, 15), (23, 15),
            (21, 30), (22, 30), (23, 30),
            (21, 45), (22, 45), (23, 45),
        ])

        group = Group.objects.first()
        actual = group.return_posting_time_list(interval=15)

        assert expected == actual
