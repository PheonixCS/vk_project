from django.test import TestCase

from posting.core.poster import prepare_audio_attachments


class Audio:
    def __init__(self, owner_id, audio_id):
        self.owner_id = owner_id
        self.audio_id = audio_id


class AudioAttachmentsTest(TestCase):
    def setUp(self):
        self.audios = [
            Audio(1, 1),
            Audio(1, 2),
            Audio(2, 1),
        ]

    def test_common(self):
        prepared_audios = prepare_audio_attachments(self.audios)

        self.assertListEqual(prepared_audios, ['audio1_1', 'audio1_2', 'audio2_1'])

    def test_cut(self):
        prepared_audios = prepare_audio_attachments(self.audios, is_cut=True)

        self.assertListEqual(prepared_audios, ['audio1_1', 'audio1_2'])

    def test_one_audio_cut(self):
        audios = [
            Audio(1, 1),
        ]

        prepared_audios = prepare_audio_attachments(audios, is_cut=True)

        self.assertListEqual(prepared_audios, ['audio1_1'])
