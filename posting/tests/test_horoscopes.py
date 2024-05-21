import os

import pytest

from posting.core.horoscopes import prepare_horoscope_with_image
from posting.core.horoscopes_images import transfer_horoscope_to_image
from posting.models import Group
from scraping.models import Horoscope

example_text = 'Овны\nБлагоприятный день. Вы настроены решительно, готовы преодолеть любые преграды, которые ' \
               'возникают на пути. Чаще обычного приходится хитрить и изворачиваться, это немного смущает, но вы '


@pytest.fixture(scope='function')
def preconditions(create_group, create_horoscope):
    group = create_group(group_type=Group.HOROSCOPES_COMMON)
    res: Horoscope = create_horoscope(group, zodiac_sign='arises', text='test horoscope \n'*10)
    return res


def test_horoscope_to_image():
    file_name = transfer_horoscope_to_image(example_text)

    assert file_name is not None
    os.remove(file_name)  # really bad


def test_horoscope_with_image_preparation(preconditions: Horoscope):
    print(preconditions.text)
    text, file = prepare_horoscope_with_image(preconditions)

    assert text == ''
    assert file is not None

    os.remove(file)  # really bad
