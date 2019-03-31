#
from django.test import TestCase
from scraping.core.helpers import extract_records_per_donor


class ExtractionTest(TestCase):
    def test_one_group_many_records(self):
        response = {
            'items': [{'owner_id': -1}, {'owner_id': -1}, {'owner_id': -1}],
            'groups': [{'id': 1}]
        }

        result = extract_records_per_donor(response)

        expected = {
            -1: [{'owner_id': -1}, {'owner_id': -1}, {'owner_id': -1}]
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
            -1: [{'owner_id': -1}, {'owner_id': -1}, {'owner_id': -1}],
            -2: [{'owner_id': -2}, {'owner_id': -2}, {'owner_id': -2}]
        }

        self.assertDictEqual(result, expected)
