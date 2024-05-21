import os

import pytest

from posting.core.horoscopes import prepare_horoscope_with_image, prepare_horoscope_cut
from posting.core.horoscopes_images import transfer_horoscope_to_image
from posting.models import Group
from scraping.models import Horoscope

example_text = 'Овны\nБлагоприятный день. Вы настроены решительно, готовы преодолеть любые преграды, которые ' \
               'возникают на пути. Чаще обычного приходится хитрить и изворачиваться, это немного смущает, но вы '

example_horoscope_postfix = 'TESTING_POSTFIX'


@pytest.fixture(scope='function')
def prepared_group(create_group):
    res: Group = create_group(group_type=Group.HOROSCOPES_COMMON, horoscope_postfix=example_horoscope_postfix)
    return res


@pytest.fixture(scope='function')
def prepared_horoscope(prepared_group, create_horoscope):
    res: Horoscope = create_horoscope(prepared_group, zodiac_sign='arises', text=example_text)
    return res


def test_horoscope_to_image():
    file_name = transfer_horoscope_to_image(example_text)

    assert file_name is not None
    os.remove(file_name)  # really bad


def test_horoscope_with_image_preparation(prepared_horoscope: Horoscope):
    text, file = prepare_horoscope_with_image(prepared_horoscope)

    assert text == ''
    assert file is not None

    os.remove(file)  # really bad


def test_horoscope_text_cut(prepared_group: Group, prepared_horoscope: Horoscope):
    text, file = prepare_horoscope_cut(prepared_group, prepared_horoscope)

    assert text.endswith(example_horoscope_postfix)
    assert file is None
