#

from django.test import TestCase

import posting.core.images as images


# Create your tests here.
class ImagesTests(TestCase):
    def test_size_calculation_width(self):
        origin_size = (1920, 1080)

        new_size = images.calculate_size_from_one_side(*origin_size, width=1280)

        self.assertEqual(new_size, (1280, 720))

    def test_size_calculation_height(self):
        origin_size = (1920, 1080)

        new_size = images.calculate_size_from_one_side(*origin_size, height=720)

        self.assertEqual(new_size, (1280, 720))
