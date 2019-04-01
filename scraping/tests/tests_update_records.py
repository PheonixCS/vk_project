# Tests for records update functions

from django.test import TestCase

from posting.models import Group
from scraping.core.scraper import update_structured_records
from scraping.models import Gif, Image, Video, Record, Donor, Audio


class UpdateFreshRecordsTest(TestCase):
    @staticmethod
    def create_record(image_count=0, audio_count=0, video_count=0, gif_count=0, **kwargs):
        group, created = Group.objects.get_or_create(domain_or_id='test')
        donor, created = Donor.objects.get_or_create(id='test')
        record = Record.objects.create(group=group, donor=donor, **kwargs)
        if image_count:
            for i in range(image_count):
                Image.objects.create(url='test', record=record)
        if audio_count:
            for i in range(audio_count):
                Audio.objects.create(url='test', record=record)
        if gif_count:
            for i in range(gif_count):
                Gif.objects.create(url='test', record=record)
        if video_count:
            for i in range(video_count):
                Video.objects.create(record=record, owner_id=123, video_id=123)

        return record

    def test_with_no_average_views(self):
        self.create_record(record_id=1)

        likes = 100
        views = 100
        reposts = 100

        data = {
            'test': [
                {
                    'id': 1,
                    'likes': {
                        'count': likes
                    },
                    'views': {
                        'count': views
                    },
                    'reposts': {
                        'count': reposts
                    }
                }
            ]
        }

        update_structured_records(data)

        record = Record.objects.first()

        self.assertEqual(record.likes_count, likes)
        self.assertEqual(record.reposts_count, reposts)
        self.assertEqual(record.views_count, views)
        self.assertEqual(record.rate, 1800)

    def test_with_average_views(self):
        self.create_record(record_id=1)

        likes = 100
        views = 100
        reposts = 100

        donor = Donor.objects.first()
        donor.average_views_number = 100
        donor.save()

        data = {
            'test': [
                {
                    'id': 1,
                    'likes': {
                        'count': likes
                    },
                    'views': {
                        'count': views
                    },
                    'reposts': {
                        'count': reposts
                    }
                }
            ]
        }

        update_structured_records(data)

        record = Record.objects.first()

        self.assertEqual(record.likes_count, likes)
        self.assertEqual(record.reposts_count, reposts)
        self.assertEqual(record.views_count, views)
        self.assertEqual(record.rate, 1000)
