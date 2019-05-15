# functions to store scraping statistics
from posting.models import PostingHistory, Group
from scraping.models import Record
from django.db.models import QuerySet


def save_posting_history(group: Group, record: Record, candidates: QuerySet) -> PostingHistory:

    candidates_str = str(list(candidates.values_list('id', flat=True)))
    candidates_number = int(candidates.count())

    obj = PostingHistory.objects.create(
        group=group,
        record=record,
        candidates_internal_ids=candidates_str,
        candidates_number=candidates_number
    )
    return obj
