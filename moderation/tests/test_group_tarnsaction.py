from moderation.core.helpers import group_transactions_by_group_id
from moderation.models import WebhookTransaction
import pytest
import json


@pytest.fixture
def create_transaction():
    transactions = []

    def _create_transaction(_id=None, **kwargs):
        _id = _id or len(transactions) + 1

        data = {'group_id': _id}

        tr = WebhookTransaction.objects.create(
            body=json.loads(json.dumps(data)),
            **kwargs
        )
        transactions.append(tr)
        return tr

    yield _create_transaction


def test_common(create_transaction):
    create_transaction(1)
    create_transaction(2)

    result = group_transactions_by_group_id(WebhookTransaction.objects.all())

    assert len(list(result.keys())) == 2

    assert len(result[1]) == 1
    assert len(result[2]) == 1


def test_one_group(create_transaction):
    create_transaction(1)
    create_transaction(1)
    create_transaction(1)

    result = group_transactions_by_group_id(WebhookTransaction.objects.all())

    assert len(list(result.keys())) == 1

    assert len(result[1]) == 3

    assert result[1][0] != result[1][1]
