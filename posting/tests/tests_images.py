#

from django.test import TestCase
from PIL import Image

import posting.core.images as images
from django.conf import settings
import os


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

        img = Image.new('RGB', (500, 500), color='white')
        img.save(image_name)

        text = '20 of seasdfasdfasdfasdfasdfasdfasdfasdfasdfaptember, Text\nLol kek\nCheburek'

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

    def test_abstraction(self):
        template_image = os.path.join(settings.BASE_DIR, 'posting/extras/image_templates', 'disc_template.png')
        result = images.paste_abstraction_on_template(template_image, 'pic.jpg')
        self.assertIsNotNone(result)
