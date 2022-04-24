from datetime import timedelta

from django.utils import timezone

from posting.tasks.examine_groups import find_common_record_to_post
from scraping.models import Record


def test_common_max_record(create_group, create_donor, create_record):
    time_threshold = timezone.now() - timedelta(hours=6)
    group = create_group()
    donor = create_donor()
    group.donors.add(donor)
    group.save()

    for i in range(10):
        create_record(group, donor, status=Record.READY, post_in_donor_date=time_threshold, rate=i * 10)

    record, candidates = find_common_record_to_post(group)

    assert record.record_id == 10
    assert record.rate == 90
    assert len(candidates) == 10


# def test_wide_time(create_group, create_donor, create_record, freezer):
#     freezer.move_to('2020-09-09 12:00:00')
#     time_threshold = timezone.now().replace(hour=0, minute=5, second=0)  # 00:05 hour posts
#     group = create_group()
#     donor = create_donor()
#     group.donors.add(donor)
#     group.save()
#
#     for i in range(10):
#         create_record(group, donor, status=Record.READY, post_in_donor_date=time_threshold, rate=i * 10)
#
#     record, candidates = find_common_record_to_post(group)
#
#     assert record.record_id == 10
#     assert record.rate == 90
#     assert len(candidates) == 10

# todo
# def test_posting_base_on_sex():
#     pass

#
