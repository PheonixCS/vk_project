#

from django.test import TestCase
from services.horoscopes.mailru import MailRuHoroscopes
from scraping.core.horoscopes import save_horoscope_for_main_groups
from posting.models import Group
from scraping.models import Horoscope, Attachment
from constance.test import override_config

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


@override_config(MAIN_HOROSCOPES_IDS='[1, 2]')
class HoroscopesSaveTest(TestCase):
    @staticmethod
    def create_groups(number=3):
        for i in range(number):
            _ = Group.objects.create(domain_or_id=str(i), group_id=i)

    @staticmethod
    def create_horoscope():
        HoroscopesSaveTest.create_groups(3)
        horoscope = Horoscope.objects.create(
            text='test',
            group=Group.objects.get(domain_or_id='0'),
            zodiac_sign='Овен'
        )
        return horoscope

    def test_saving(self):
        test_horoscope = self.create_horoscope()
        # print(Group.objects.all())

        save_horoscope_for_main_groups(test_horoscope, image_vk_url='test_vk_image')

        self.assertEqual(Horoscope.objects.count(), 3)
        self.assertEqual(Attachment.objects.count(), 2)

        for horo in Horoscope.objects.filter(group__group_id__in=[1, 2]):
            self.assertEqual(horo.attachments.count(), 1)
            self.assertEqual(horo.attachments.filter(data_type=Attachment.PICTURE).first().vk_attachment_id,
                             'test_vk_image')

