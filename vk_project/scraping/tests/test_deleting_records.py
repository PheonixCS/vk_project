# test for periodic deleting tasks
from datetime import datetime, timedelta

from constance.test import override_config
from django.test import TestCase
from django.utils import timezone

from posting.models import Group
from scraping.models import Record, Gif, Image, Video, Audio, Donor
from scraping.tasks import delete_oldest


@override_config(COMMON_RECORDS_COUNT_FOR_DONOR=3)
class DeletingTests(TestCase):
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

    def test_delete_oldest(self):
        for i in range(5):
            self.create_record()

        delete_oldest()

        self.assertEqual(Record.objects.all().count(), 3)

    def test_delete_no_records(self):
        for i in range(2):
            self.create_record()

        delete_oldest()

        self.assertEqual(Record.objects.all().count(), 2)

    def test_check_time(self):
        now = datetime.now(tz=timezone.utc)
        offset = now - timedelta(days=1)

        self.create_record(post_in_donor_date=now)
        self.create_record(post_in_donor_date=now)
        self.create_record(post_in_donor_date=now)
        self.create_record(post_in_donor_date=offset)

        delete_oldest()

        self.assertEqual(Record.objects.all().count(), 3)
        self.assertEqual(Record.objects.filter(post_in_donor_date__lt=now).exists(), 0)
