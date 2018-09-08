#

from django.test import TestCase
from posting import poster


# Create your tests here.
class ImagesTests(TestCase):

    # def test_merging(self):
    #     files = ['{}test.jpg'.format(num) for num in range(1, 7)]
    #     result = poster.merge_six_images_into_one(files)
    #
    #     self.assertEqual(result, 'temp_1test.jpg')

    def test_size_calculation_width(self):
        origin_size = (1920, 1080)

        new_size = poster.calculate_size(*origin_size, width=1280)

        self.assertEqual(new_size, (1280, 720))

    def test_size_calculation_height(self):
        origin_size = (1920, 1080)

        new_size = poster.calculate_size(*origin_size, height=720)

        self.assertEqual(new_size, (1280, 720))
