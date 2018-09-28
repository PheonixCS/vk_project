#

from django.test import TestCase
from posting import poster


class Record:
    def __init__(self, rate, ratio):
        self.rate = rate
        self.males_females_ratio = ratio

    def __str__(self):
        return '{}_{}'.format(self.rate, self.males_females_ratio)


class BestRecordTest(TestCase):
    def test_common(self):
        records = [
            Record(500, 1.33),
            Record(800, 1.83),
            Record(500, 0.61),
            Record(200, 2.61),
            Record(900, 0.32)
        ]
        best_record = poster.find_the_best_post(records, 1.8, 50)

        self.assertEqual(best_record.rate, 800)
        self.assertEqual(best_record.males_females_ratio, 1.83)

    def test_no_match(self):
        records = [
            Record(100, 1.33),
            Record(200, 0.83),
            Record(300, 1.61),
            Record(400, 1.80),
            Record(600, 0.33),
            Record(600, 1.66)
        ]
        best_record = poster.find_the_best_post(records, 0.5, 50)

        self.assertEqual(best_record.rate, 600)
        self.assertEqual(best_record.males_females_ratio, 0.33)

    def test_equal_ratio_best_rate(self):
        records = [
            Record(100, 1.33),
            Record(200, 1.83),
            Record(700, 0.33),
            Record(300, 1.44),
            Record(300, 1.86),
            Record(400, 1.22),
            Record(600, 1.22),
            Record(900, 1.22),
        ]
        best_record = poster.find_the_best_post(records, 1.6, 50)

        self.assertEqual(best_record.rate, 900)
        self.assertEqual(best_record.males_females_ratio, 1.22)
