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

    def test_text_on_images(self):
        image_name = 'test.jpg'
        text = '20 of september, Text'

        images.paste_text_on_image(image_name, text, position='top')

        self.assertTrue(True)

    def test_position_calculation(self):
        image_box = (100, 100)
        text_box = (20, 5)

        position = images.calculate_text_position_on_image(image_box, text_box, 'top')

        self.assertEqual(position, (40, 10))

    def test_position_calculation_bottom(self):
        image_box = (100, 100)
        text_box = (20, 5)

        position = images.calculate_text_position_on_image(image_box, text_box, 'bottom')

        self.assertEqual(position, (40, 85))
