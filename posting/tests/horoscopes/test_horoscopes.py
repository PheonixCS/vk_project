import os

import pytest

from posting.core.horoscopes import prepare_horoscope_with_image, prepare_horoscope_cut
from posting.core.horoscopes_images import transfer_horoscope_to_image
from posting.models import Group
from scraping.core.horoscopes import get_horoscopes_emoji
from scraping.models import Horoscope

example_text = 'Овны\nБлагоприятный день. Вы настроены решительно, готовы преодолеть любые преграды, которые ' \
               'возникают на пути. Чаще обычного приходится хитрить и изворачиваться, это немного смущает, но вы '

example_horoscope_postfix = 'TESTING_POSTFIX'

example_text_with_data = '29 мая, рыбы\nЗавтра Рыб могут одолевать самые разные нескромные желания, '\
                         'которые они захотят скрыть от окружающих. '\
                         'Возможны любые вариации на тему семи смертных грехов. Внутренняя борьба с собой способна '\
                         'отнять всё внимание Рыб, вплоть до того, что они будут казаться окружающим этаким Каем '\
                         'вовремя пребывания в плену...'

@pytest.fixture(scope='function')
def prepared_group(create_group):
    res: Group = create_group(group_type=Group.HOROSCOPES_COMMON, horoscope_postfix=example_horoscope_postfix)
    return res


@pytest.fixture(scope='function')
def prepared_horoscope(prepared_group, create_horoscope):
    res: Horoscope = create_horoscope(prepared_group, zodiac_sign='arises', text=example_text)
    return res


@pytest.fixture(scope='function')
def prepared_horoscope_pisces(prepared_group, create_horoscope):
    res: Horoscope = create_horoscope(prepared_group, zodiac_sign='pisces', text=example_text_with_data)
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


def test_horoscope_with_text_cut_prefix(prepared_group: Group, prepared_horoscope: Horoscope):
    text, file = prepare_horoscope_cut(prepared_group, prepared_horoscope)

    assert text.endswith(f'... {example_horoscope_postfix}')
    assert len(text) < len(prepared_horoscope.text)
    assert file is None


def test_horoscope_with_text_cut_words(prepared_group: Group, prepared_horoscope: Horoscope):
    prepared_horoscope.text = 'one\ntwo three four\nfive six'
    prepared_horoscope.save()

    expected = f'ONE &#9800;\n\ntwo... {prepared_group.horoscope_postfix}'

    text, _ = prepare_horoscope_cut(prepared_group, prepared_horoscope)

    assert text == expected


def test_horoscope_with_text_cut_file(prepared_group: Group, prepared_horoscope: Horoscope):
    _, file = prepare_horoscope_cut(prepared_group, prepared_horoscope)

    assert file is None


def test_horoscope_text_upper_first_sentence(prepared_group: Group, prepared_horoscope_pisces: Horoscope):
    text, file = prepare_horoscope_cut(prepared_group, prepared_horoscope_pisces)
    first_part = prepared_horoscope_pisces.text.split(f"\n")[0]

    assert first_part.upper() == text.split(f" &#9811;\n")[0]


def test_horoscope_text_with_two_line_breaks_after_zodiac_sign(prepared_group: Group,
                                                               prepared_horoscope_pisces: Horoscope):
    text, file = prepare_horoscope_cut(prepared_group, prepared_horoscope_pisces)
    zodiac_sign_index_end = text.rfind(";")
    assert text[zodiac_sign_index_end+1:zodiac_sign_index_end+3] == "\n\n"


def test_horoscope_text_contains_zodiac_emoji(prepared_group: Group, prepared_horoscope_pisces: Horoscope):
    text, file = prepare_horoscope_cut(prepared_group, prepared_horoscope_pisces)
    zodiac_emoji = text.split("\n\n")[0].split(" ")[-1]

    assert get_horoscopes_emoji(prepared_horoscope_pisces.zodiac_sign) == zodiac_emoji

