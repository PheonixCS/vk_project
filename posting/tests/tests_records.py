#

from django.test import TestCase
from posting import poster


class Record:
    def __init__(self, rate, ratio):
        self.rate = rate
        self.males_females_ratio = ratio


class BestRecordTest(TestCase):
    def test_common(self):
        records = [
            Record(300, 1.33123),
            Record(200, 1.83213),
            Record(200, 1.61234)
        ]
        best_record = poster.find_the_best_post(records, 1.8)

        self.assertEqual(best_record.rate, 200)
        self.assertEqual(best_record.males_females_ratio, 1.83213)

    def test_no_match(self):
        records = [
            Record(100, 1.33123),
            Record(200, 1.83213),
            Record(200, 1.61234)
        ]
        best_record = poster.find_the_best_post(records, 1.7)

        self.assertEqual(best_record.rate, 200)
        self.assertEqual(best_record.males_females_ratio, 1.83213)

    def test_equal_ratio_best_rate(self):
        records = [
            Record(100, 1.331),
            Record(200, 1.832),
            Record(200, 1.612),
            Record(400, 1.686)
        ]
        best_record = poster.find_the_best_post(records, 1.6)

        self.assertEqual(best_record.rate, 400)
        self.assertEqual(best_record.males_females_ratio, 1.686)

    def test_ratio_less_one(self):
        records = [
            Record(200, 0.33123),
            Record(200, 0.83213),
            Record(200, 0.61234)
        ]
        best_record = poster.find_the_best_post(records, 0.5)

        self.assertEqual(best_record.rate, 200)
        self.assertEqual(best_record.males_females_ratio, 0.33123)
