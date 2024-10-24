#
from django.test import TestCase

from services.text_utilities import replace_russian_with_english_letters


class TestTextReplacement(TestCase):

    def test_base_replacement(self):
        origin_text = 'Как же так'
        expected_text = 'Кaк жe тaк'
        result = replace_russian_with_english_letters(origin_text)
        self.assertEqual(result, expected_text,
                         '{}\n{}'.format([ord(i) for i in result], [ord(i) for i in expected_text]))

    def test_hashtag_ignore(self):
        origin_text = 'Это #хэштэг на тест'
        expected_text = 'Этo #хэштэг нa тecт'
        result = replace_russian_with_english_letters(origin_text)
        self.assertEqual(result, expected_text,
                         '{}\n{}'.format([ord(i) for i in result], [ord(i) for i in expected_text]))
