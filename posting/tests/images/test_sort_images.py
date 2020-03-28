from posting.core.images import sort_images_for_movies


def test_common_order():
    images = ['testing/files/test50x60.png',
              'testing/files/test60x50.png',
              'testing/files/test50x40.png']  # vertical first
    sorted_images = sort_images_for_movies(images)

    assert sorted_images == images, \
        f'Expected {images},\nGot {sorted_images}'


def test_reverse():
    images = ['testing/files/test50x40.png',
              'testing/files/test60x50.png',
              'testing/files/test50x60.png']  # vertical last
    expect = ['testing/files/test50x60.png',
              'testing/files/test60x50.png',
              'testing/files/test50x40.png']  # vertical first
    sorted_images = sort_images_for_movies(images)

    assert sorted_images == expect, \
        f'Expected {expect},\nGot {sorted_images}'


def test_no_horizontal():
    images = ['testing/files/test50x60.png',
              'testing/files/test60x50.png']
    sorted_images = sort_images_for_movies(images)

    assert sorted_images == images, \
        f'Expected {images},\nGot {sorted_images}'


def test_in_the_middle():
    images = ['testing/files/test50x40.png',
              'testing/files/test50x60.png',
              'testing/files/test60x50.png']  # vertical in the middle
    expect = ['testing/files/test50x60.png',
              'testing/files/test50x40.png',
              'testing/files/test60x50.png']  # vertical first
    sorted_images = sort_images_for_movies(images)

    assert sorted_images == expect, \
        f'Expected {expect},\nGot {sorted_images}'
