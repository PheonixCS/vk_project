from posting.core.horoscopes_images import transfer_horoscope_to_image
import os

example_text = 'Овны\nБлагоприятный день. Вы настроены решительно, готовы преодолеть любые преграды, которые ' \
               'возникают на пути. Чаще обычного приходится хитрить и изворачиваться, это немного смущает, но вы '


def test_horoscope_to_image():
    file_name = transfer_horoscope_to_image(example_text)

    assert file_name is not None
    os.remove(file_name)
