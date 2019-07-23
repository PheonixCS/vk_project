#
from django.test import TestCase
from constance.test import override_config
from datetime import date

from scraping.core.helpers import extract_records_per_donor, is_donor_out_of_date, find_newest_record


class ExtractionTest(TestCase):
    def test_one_group_many_records(self):
        response = {
            'items': [{'owner_id': -1}, {'owner_id': -1}, {'owner_id': -1}],
            'groups': [{'id': 1}]
        }

        result = extract_records_per_donor(response)

        expected = {
            1: [{'owner_id': -1}, {'owner_id': -1}, {'owner_id': -1}]
        }

        self.assertDictEqual(result, expected)

    def test_many_groups_many_records(self):
        response = {
            'items': [{'owner_id': -1}, {'owner_id': -1}, {'owner_id': -1},
                      {'owner_id': -2}, {'owner_id': -2}, {'owner_id': -2}],
            'groups': [{'id': 1}, {'id': 2}]
        }

        result = extract_records_per_donor(response)

        expected = {
            1: [{'owner_id': -1}, {'owner_id': -1}, {'owner_id': -1}],
            2: [{'owner_id': -2}, {'owner_id': -2}, {'owner_id': -2}]
        }

        self.assertDictEqual(result, expected)


class OutdatedDonorsTests(TestCase):
    def setUp(self):
        self.date_to_compare = date.fromtimestamp(1561507200)  # 26.06.2019

    def test_acting_donor(self):
        newest_record_date = 1561507200  # 26.06.2019
        self.assertFalse(is_donor_out_of_date(newest_record_date, self.date_to_compare))

        newest_record_date = 1561334400  # 24.06.2019
        self.assertFalse(is_donor_out_of_date(newest_record_date, self.date_to_compare))

    def test_outdated_donor(self):
        newest_record_date = 1557532800  # 11.05.2019
        self.assertTrue(is_donor_out_of_date(newest_record_date, self.date_to_compare))

        newest_record_date = 1558742400  # 25.05.2019
        self.assertTrue(is_donor_out_of_date(newest_record_date, self.date_to_compare))


class NewestRecordTests(TestCase):
    def test_no_records(self):
        records = []
        self.assertEqual(find_newest_record(records), {})

    def test_pinned_record(self):
        records = [
            {'is_pinned': False, 'date': 1561334400},
            {'is_pinned': False, 'date': 1557532800},
            {'is_pinned': True, 'date': 1561507200},
        ]
        newest_record = find_newest_record(records)
        self.assertEqual(len(newest_record), 1)
        self.assertDictEqual(newest_record, {'is_pinned': False, 'date': 1561334400})

    def test_default_records(self):
        records = [
            {'is_pinned': False, 'date': 1561334400},
            {'is_pinned': False, 'date': 1557532800},
        ]
        newest_record = find_newest_record(records)
        self.assertEqual(len(newest_record), 1)
        self.assertDictEqual(newest_record, {'is_pinned': False, 'date': 1561334400})
