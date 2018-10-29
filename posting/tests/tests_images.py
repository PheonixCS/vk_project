#

from django.test import TestCase
from posting import poster
from posting.core import horoscopes_images


# Create your tests here.
class ImagesTests(TestCase):

    # def test_merging(self):
    #     files = ['{}test.jpg'.format(num) for num in range(1, 7)]
    #     result = poster.merge_six_images_into_one(files)
    #
    #     self.assertEqual(result, 'temp_1test.jpg')

    def test_size_calculation_width(self):
        origin_size = (1920, 1080)

        new_size = poster.calculate_size_from_one_side(*origin_size, width=1280)

        self.assertEqual(new_size, (1280, 720))

    def test_size_calculation_height(self):
        origin_size = (1920, 1080)

        new_size = poster.calculate_size_from_one_side(*origin_size, height=720)

        self.assertEqual(new_size, (1280, 720))

    def test_horoscope_image(self):
        text = '20 of september, Text\n' \
               'Нестабильный, двойственный день, он будет намного лучше, если вы сможете заранее его спланировать. ' \
               'В этот день не рекомендуюся перестановки в доме, начало новых дел, смена места работы или проживания.' \
               'Постарайтесь избегать сегодня проявления негативных эмоций и агрессии, пусть в вашей душе царит покой' \
               ' и равновесие.'

        file_name = 'horoscopes{}.jpg'.format(hash(text) % 1000)

        result = horoscopes_images.transfer_horoscope_to_image(text)

        self.assertEqual(result, file_name)
