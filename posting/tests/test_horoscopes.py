from django.test import TestCase

from posting.core.horoscopes_images import transfer_horoscope_to_image


class HoroscopeImagesTests(TestCase):
    example_text = 'Овны\nБлагоприятный день. Вы настроены решительно, готовы преодолеть любые преграды, которые ' \
                   'возникают на пути. Чаще обычного приходится хитрить и изворачиваться, это немного смущает, но вы '

    def test_common(self):
        file_name = transfer_horoscope_to_image(self.example_text)

        self.assertIsNotNone(file_name)
