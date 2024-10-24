import pytest
from django.test import TestCase

from posting.core.poster import prepare_audio_attachments


class Audio:
    def __init__(self, owner_id, audio_id):
        self.owner_id = owner_id
        self.audio_id = audio_id


@pytest.mark.django_db
class AudioAttachmentsTest(TestCase):
    def setUp(self):
        self.audios = [
            Audio(1, 1),
            Audio(1, 2),
            Audio(2, 1),
        ]

    def test_common(self):
        result = prepare_audio_attachments(self.audios)

        expected = ['audio1_1', 'audio1_2', 'audio2_1']

        self.assertListEqual(result, expected)

    def test_no_audios(self):
        audios = []

        result = prepare_audio_attachments(audios, is_shuffle=True, is_cut=True)

        expected = []

        self.assertEqual(result, expected)

    def test_cut(self):
        result = prepare_audio_attachments(self.audios, is_cut=True)

        expected = ['audio1_1', 'audio1_2']

        self.assertListEqual(result, expected)

    def test_one_audio_cut(self):
        audios = [
            Audio(1, 1),
        ]

        result = prepare_audio_attachments(audios, is_cut=True)

        expected = ['audio1_1']

        self.assertListEqual(result, expected)
