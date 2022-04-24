import re

from moderation.core.checks import is_scam_words_in_text


def test_has_scam_words():
    text = 'Это такой теst'
    words_in_text = re.sub(r'[^\w]', ' ', text).split()

    actual = is_scam_words_in_text(words_in_text) is not None
    expected = True

    assert actual is expected, \
        f'Actual result is {actual} in text: "{text}"'


def test_has_no_scam_words():
    text = 'Это такой тест'
    words_in_text = re.sub(r'[^\w]', ' ', text).split()

    actual = is_scam_words_in_text(words_in_text) is not None
    expected = False

    assert actual is expected, \
        f'Actual result is {actual} in text: "{text}"'
