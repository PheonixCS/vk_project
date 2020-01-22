from constance.test import override_config
from django.test import TestCase

from scraping.core.filters import filter_out_records_with_small_images, filter_out_ads


@override_config(MIN_QUANTITY_OF_PIXELS=500)
class ImagesSizeTests(TestCase):
    def test_default_case(self):
        records = [
            {
                'id': 1,
                'attachments': [
                    {
                        'photo': {
                            'width': 1000,
                            'height': 700,
                        },
                        'type': 'photo'
                    },
                    {
                        'photo': {
                            'width': 1200,
                            'height': 800,
                        },
                        'type': 'photo'
                    },
                ]
            },
            {
                'id': 2,
                'attachments': [
                    {
                        'photo': {
                            'width': 1200,
                            'height': 800,
                        },
                        'type': 'photo'
                    },
                    {
                        'photo': {
                            'width': 500,
                            'height': 250,
                        },
                        'type': 'photo'
                    },
                ]
            },
            {
                'id': 3,
                'attachments': [
                    {
                        'video': {
                            'video_id': 123,
                        },
                        'type': 'video'
                    },
                ]
            },
            {
                'id': 4,
            }
        ]

        filtered_records = filter_out_records_with_small_images(records)

        self.assertEqual(len(filtered_records), 3)

    def test_no_images(self):
        records = [
            {
                'id': 1,
                'attachments': [
                    {
                        'video': {
                            'video_id': 123,
                        },
                        'type': 'video'
                    },
                ]
            }
        ]

        filtered_records = filter_out_records_with_small_images(records)

        self.assertListEqual(filtered_records, records)

    def test_no_attachments(self):
        records = [{'id': 1}, {'id': 2}]

        filtered_records = filter_out_records_with_small_images(records)

        self.assertListEqual(filtered_records, records)

    def test_images_without_dimensions(self):
        records = [
            {
                'id': 1
            },
            {
                'id': 2,
                'attachments': [
                    {
                        'photo': {},
                        'type': 'photo'
                    },
                ]
            }
        ]
        
        filtered_records = filter_out_records_with_small_images(records)
        
        self.assertEqual(len(filtered_records), 2)

    def test_ads_filter_vk_link(self):
        records = [
            {
                'id': 1,
                'text': '👉🏻vk.com/zakulyska - подписывайтесь сюда, чтобы попасть!'
            }
        ]

        filtered = filter_out_ads(records)

        self.assertEqual(len(filtered), 0)
