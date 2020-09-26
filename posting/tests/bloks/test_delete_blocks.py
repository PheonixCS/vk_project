from posting.tasks.delete_old_blocks import delete_old_blocks
from posting.models import Block


def test_deleting(create_group, freezer):
    group = create_group()
    freezer.move_to('2020-09-09 12:00:00')

    group.set_block(reason=Block.AD, period_in_minutes=65)

    freezer.move_to('2020-09-14 12:00:00')
    group.is_blocked()

    blocks_deleted = delete_old_blocks()

    assert blocks_deleted == 1
