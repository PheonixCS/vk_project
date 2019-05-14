# functions to store scraping statistics
from posting.models import PostingHistory


def save_posting_history(group, record, candidates):

    candidates_str = candidates.values_list('id', flat=True)

    obj = PostingHistory.objects.create(
        group=group,
        record=record,
        candidates_internal_ids=candidates_str,
        candidates_number=candidates.count()
    )
    return obj
