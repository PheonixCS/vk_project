#

from django.test import TestCase
from posting.core import poster


class Record:
    def __init__(self, rate, ratio):
        self.rate = rate
        self.males_females_ratio = ratio

    def __str__(self):
        return '{}_{}'.format(self.rate, self.males_females_ratio)


class SuitableRecordTest(TestCase):
    def test_exact_record(self):
        records = [
            Record(500, 40/60),
            Record(600, 50/60),
            Record(700, 40/60),
            Record(800, 40/60),
            Record(900, 40/60)
        ]
        best_record = poster.find_suitable_record(records, 40/60)

        self.assertEqual(best_record.rate, 900)

    def test_no_suitable(self):
        records = [
            Record(500, 70/30),
            Record(600, 70/30),
            Record(700, 70/30),
        ]
        best_record = poster.find_suitable_record(records, 40/60)

        self.assertEqual(best_record.rate, 700)

    def test_in_range(self):
        records = [
            Record(500, 70/30),
            Record(600, 49/51),
            Record(700, 70/30),
        ]
        best_record = poster.find_suitable_record(records, 40/60)

        self.assertEqual(best_record.rate, 600)

    def test_custom_range_no_suitable(self):
        records = [
            Record(500, 70/30),
            Record(600, 70/30),
            Record(700, 70/30),
        ]
        best_record = poster.find_suitable_record(records, 40/60, 10)

        self.assertEqual(best_record.rate, 700)

    def test_custom_range_suitable(self):
        records = [
            Record(500, 70/30),
            Record(600, 70/30),
            Record(700, 49/51),
        ]
        best_record = poster.find_suitable_record(records, 40/60, 10)

        self.assertEqual(best_record.rate, 700)
