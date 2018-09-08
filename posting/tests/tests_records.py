#

from django.test import TestCase
from posting import poster


class Record:
    def __init__(self, rate, ratio):
        self.rate = rate
        self.ratio = ratio


class BestRecordTest(TestCase):
    def test_common(self):
        records = [
            Record(300, 1.33123),
            Record(200, 1.83213),
            Record(200, 1.61234)
        ]
        best_record = poster.find_the_best_post(records, 1.8)

        self.assertEqual(best_record.rate, 200)
        self.assertEqual(best_record.ratio, 1.83213)

    def test_no_match(self):
        records = [
            Record(100, 1.33123),
            Record(200, 1.83213),
            Record(200, 1.61234)
        ]
        best_record = poster.find_the_best_post(records, 1.7)

        self.assertEqual(best_record.rate, 200)
        self.assertEqual(best_record.ratio, 1.83213)

    def test_equal_ratio_best_rate(self):
        records = [
            Record(100, 1.331),
            Record(200, 1.832),
            Record(200, 1.612),
            Record(400, 1.686)
        ]
        best_record = poster.find_the_best_post(records, 1.6)

        self.assertEqual(best_record.rate, 400)
        self.assertEqual(best_record.ratio, 1.686)
