# test for records filtration
from django.test import TestCase
from posting.core import poster
from scraping.models import Record, Gif, Image, Video, Audio, Donor
from posting.models import Group


class FiltrationTests(TestCase):
    def create_record(self, image_count=0, audio_count=0, video_count=0, gif_count=0):
        group, created = Group.objects.get_or_create(domain_or_id='test')
        donor, created = Donor.objects.get_or_create(id='test')
        record = Record.objects.create(group=group, donor=donor)
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

    def test_filter_image(self):
        self.create_record(image_count=3)
        r = Record.objects.all()
        result = poster.filter_banned_records(r, ['picture', ])

        self.assertEqual(len(result), 0)

    def test_filter_gif(self):
        self.create_record(gif_count=2)
        r = Record.objects.all()

        result = poster.filter_banned_records(r, ['gif', ])
        self.assertEqual(len(result), 0)

    def test_filter_video(self):
        self.create_record(video_count=1)
        r = Record.objects.all()

        result = poster.filter_banned_records(r, ['video', ])
        self.assertEqual(len(result), 0)

    def test_multi_filtration(self):
        self.create_record(image_count=1)
        self.create_record(video_count=1)
        r = Record.objects.all()

        result = poster.filter_banned_records(r, ['video', 'picture'])
        self.assertEqual(len(result), 0)

    def test_zero_filtration(self):
        self.create_record(image_count=3)
        self.create_record(image_count=2, gif_count=1)
        r = Record.objects.all()

        result = poster.filter_banned_records(r, ['video', ])

        self.assertEqual(len(result), 2)
