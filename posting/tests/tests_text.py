#
from django.test import TestCase

from posting.text_utilities import replace_russian_with_english_letters


class TestTextReplacement(TestCase):
    def test_base_replacement(self):
        original_text = 'Вот такие дела'
        expected_text = 'Bот такие дeла'
        result = replace_russian_with_english_letters(original_text)
        self.assertEqual(result, expected_text,
                         '{}\n{}'.format([ord(i) for i in result], [ord(i) for i in expected_text]))

    def test_word_without_needed_letters(self):
        original_text = 'клён выжил'
        expected_text = 'клён выжил'
        result = replace_russian_with_english_letters(original_text)
        self.assertEqual(result, expected_text,
                         '{}\n{}'.format([ord(i) for i in result], [ord(i) for i in expected_text]))

    def test_multi_line(self):
        original_text = 'как\nмне\nвыжить?'
        expected_text = 'кaк\nмне\nвыжить?'
        result = replace_russian_with_english_letters(original_text)
        self.assertEqual(result, expected_text,
                         '{}\n{}'.format([ord(i) for i in result], [ord(i) for i in expected_text]))

    def test_duplicates(self):
        original_text = 'тест тест 12 тест тест'
        expected_text = 'тeст тест 12 тeст тест'
        result = replace_russian_with_english_letters(original_text)
        self.assertEqual(result, expected_text,
                         '{}\n{}'.format([ord(i) for i in result], [ord(i) for i in expected_text]))
