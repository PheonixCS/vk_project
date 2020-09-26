from posting.models import Block


def test_activation(create_group, freezer):
    group = create_group()
    freezer.move_to('2020-09-09 12:00:00')

    group.set_block(reason=Block.AD, period_in_minutes=65)

    freezer.move_to('2020-09-09 13:00:00')
    result = group.is_blocked()

    assert result is True


def test_deactivation(create_group, freezer):
    group = create_group()
    freezer.move_to('2020-09-09 12:00:00')

    group.set_block(reason=Block.AD, period_in_minutes=65)

    freezer.move_to('2020-09-09 13:06:00')
    result = group.is_blocked()

    assert result is False


def test_activation_border(create_group, freezer):
    group = create_group()
    freezer.move_to('2020-09-09 12:00:00')

    group.set_block(reason=Block.AD, period_in_minutes=65)

    freezer.move_to('2020-09-09 13:04:59')
    result = group.is_blocked()

    assert result is True
