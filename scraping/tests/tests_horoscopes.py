#

from django.test import TestCase
from services.horoscopes.mailru import MailRuHoroscopes


from unittest import mock


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, test):
            self.text = test
            self.headers = ''

        def raise_for_status(self):
            pass

    mocked_text = """
<div class="article__text">
    <div class="article__item article__item_alignment_left article__item_html">
        <p>test</p>
        <p>test</p>
    </div>
</div>
"""
    return MockResponse(mocked_text)


class MailHoroscopesTest(TestCase):
    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_is_alive(self, mock_get):
        horo = MailRuHoroscopes()

        result = horo.parse()

        self.assertEqual(len(result), 12)


# class HoroscopesHelpers(TestCase):
#     def test_tran