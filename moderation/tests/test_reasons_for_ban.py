from moderation.core.process_comment import check_for_reason_for_ban_and_get_comments_to_delete
import pytest


# @pytest.fixture
# def create_comment():
#     comments = []
#
#     def _create_comment(group, donor, **kwargs):
#         comment_id = len(comments) + 1
#
#         # group, created = Record.objects.get_or_create(
#         #     donor=donor,
#         #     group=group,
#         #     record_id=comment_id,
#         #     **kwargs
#         # )
#         comments.append(group)
#         return group
#
#     yield _create_comment


class StubComment:
    def __init__(self, _id=None, from_id=None):
        self.id = _id
        self.from_id = from_id

    def __getitem__(self, item):
        return self.__getattribute__(item)


def test_group():
    comment = StubComment(1, -123)

    actual = check_for_reason_for_ban_and_get_comments_to_delete(comment)
    expected = 'группа', [1, ]

    assert actual == expected

# def test_audio_and_photo():
#     pass
#
#
# def test_many_identical_texts():
#     pass
#
#
# def test_many_identical_attaches():
#     pass
