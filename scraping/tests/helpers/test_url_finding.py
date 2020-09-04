from scraping.core.helpers import find_url_of_biggest_image


def test_common_behaviour():
    image = {
        'photo_75': 'false',
        'photo_130': 'false',
        'photo_604': 'false',
        'photo_807': 'false',
        'photo_1280': 'biggest',
    }

    expected = 'biggest'
    actual = find_url_of_biggest_image(image)

    assert actual == expected


def test_medium_size():
    image = {
        'photo_75': 'false',
        'photo_130': 'false',
        'photo_1280': 'biggest',
        'photo_604': 'false',
        'photo_807': 'false'
    }

    expected = 'biggest'
    actual = find_url_of_biggest_image(image)

    assert actual == expected
