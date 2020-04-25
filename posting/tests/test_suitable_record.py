from posting.core.poster import find_suitable_record
import pytest
from scraping.models import Record, Donor

from posting.models import Group

pytestmark = pytest.mark.django_db(transaction=True, reset_sequences=True)


@pytest.fixture(scope='function')
def create_record():
    group = Group.objects.create(group_id=1)
    donor = Donor.objects.create(id='1')

    def _create_record(*args, **kwargs):
        res = Record.objects.create(group=group, donor=donor, *args, **kwargs)

        return res

    yield _create_record

    group.delete()
    donor.delete()
    Record.objects.all().delete()


def test_common_records(create_record):
    create_record(rate=100, females_count=10, males_count=10)
    create_record(rate=200, females_count=10, males_count=10)
    create_record(rate=300, females_count=10, males_count=10)

    records = Record.objects.all()

    result = find_suitable_record(records, (0.5, 0.5), divergence=0)

    assert result.id == 3


def test_default_record(create_record):
    create_record(rate=101, females_count=30, males_count=70)
    create_record(rate=100, females_count=40, males_count=60)
    create_record(rate=100, females_count=40, males_count=60)

    records = Record.objects.all()

    result = find_suitable_record(records, (0.5, 0.5), divergence=0)

    assert result.id == 1


def test_percent_record(create_record):
    create_record(rate=200, females_count=30, males_count=70)
    create_record(rate=150, females_count=30, males_count=70)
    create_record(rate=100, females_count=40, males_count=60)

    records = Record.objects.all()

    result = find_suitable_record(records, (0.5, 0.5), divergence=10)

    assert result.id == 1
