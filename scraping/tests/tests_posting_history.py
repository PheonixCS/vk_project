from django.test.utils import TestCase

from posting.models import Group
from posting.core.posting_history import save_posting_history
from scraping.models import Gif, Image, Video, Record, Donor, Audio


class SaveHistoryTest(TestCase):
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

    def test_common_saving(self):
        exclude = self.create_record(record_id=1)
        self.create_record(record_id=2)
        self.create_record(record_id=3)

        group = Group.objects.first()
        all_records = Record.objects.all()

        records_exclude = all_records
        res = save_posting_history(
            group=group,
            record=exclude,
            candidates=records_exclude
        )

        self.assertIsNotNone(res)
