# test donors average count calculation

from django.test import TestCase
from constance.test import override_config

from posting.models import Group
from scraping.models import Record, Gif, Image, Video, Audio, Donor

from scraping.tasks import set_donors_average_view


@override_config(COMMON_RECORDS_COUNT_FOR_DONOR=3)
class AverageCalcTests(TestCase):
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

    def test_common(self):
        self.create_record(views_count=500)
        self.create_record(views_count=600)
        self.create_record(views_count=700)

        set_donors_average_view()

        self.assertEqual(Donor.objects.first().average_views_number, 600)

    def test_none(self):
        self.create_record(views_count=500)
        self.create_record(views_count=600)

        set_donors_average_view()

        self.assertIsNone(Donor.objects.first().average_views_number)
