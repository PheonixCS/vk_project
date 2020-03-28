from PIL import Image

import posting.core.images as images


# Create your tests here.
class TestImages:
    def test_size_calculation_width(self):
        origin_size = (1920, 1080)

        new_size = images.calculate_size_from_one_side(*origin_size, width=1280)

        assert new_size == (1280, 720)

    def test_size_calculation_height(self):
        origin_size = (1920, 1080)

        new_size = images.calculate_size_from_one_side(*origin_size, height=720)

        assert new_size == (1280, 720)

    def test_text_on_images(self, tmp_path):
        image_name = str(tmp_path / 'test.jpg')

        img = Image.new('RGB', (500, 500), color='white')
        img.save(image_name, 'jpeg')

        text = '20 of seasdfasdfasdfasdfasdfasdfasdfasdfasdfaptember, Text\nLol kek\nCheburek'

        result = images.paste_text_on_image(image_name, text, position='top')

        assert result

    def test_position_calculation(self):
        image_box = (100, 100)
        text_box = (20, 5)

        position = images.calculate_text_position_on_image(image_box, text_box, 'top')

        assert position == (40, 10)

    def test_position_calculation_bottom(self):
        image_box = (100, 100)
        text_box = (20, 5)

        position = images.calculate_text_position_on_image(image_box, text_box, 'bottom')

        assert position == (40, 85)

    # def test_abstraction(self):
    #     template_image = os.path.join(settings.BASE_DIR, 'posting/extras/image_templates', 'disc_template.png')
    #     result = images.paste_abstraction_on_template(template_image, 'pic.jpg')
    #     self.assertIsNotNone(result)

    def test_calculate_box(self):
        size = (800, 600)
        size_two = (300, 300)
        expected_box = (250, 150, 550, 450)

        result_box = images.calculate_centered_box(size_two, size)

        assert result_box == expected_box

    def test_calculate_box_equal_size(self):
        size = (800, 600)
        size_two = (600, 600)
        expected_box = (100, 0, 700, 600)

        result_box = images.calculate_centered_box(size_two, size)

        assert result_box == expected_box

    def test_center_box(self):
        img = Image.new('RGB', (500, 500), color='white')

        result = images.crop_center(img, (300, 300))

        assert result.size == (300, 300)

    def test_position_calculation_with_offset_bottom(self):
        image_size = (100, 100)
        text_size = (20, 5)

        position = images.calculate_text_position_on_image(image_size, text_size, 'bottom', offset=10)

        assert position == (40, 75)

    def test_position_calculation_with_offset_top(self):
        image_size = (100, 100)
        text_size = (20, 5)

        position = images.calculate_text_position_on_image(image_size, text_size, 'top', offset=10)

        assert position == (40, 20)
