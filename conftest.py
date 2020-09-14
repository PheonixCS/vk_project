import logging
from datetime import timedelta

import pytest
from django.utils import timezone

from posting.models import Group
from scraping.models import Donor, Record


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(transactional_db):
    logging.disable(logging.CRITICAL)
    pass


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)


@pytest.fixture
def create_group():
    groups = []

    def _create_group(group_id=None, sex_last_update_days=7, **kwargs):
        now_time_utc = timezone.now()
        week_ago = now_time_utc - timedelta(days=sex_last_update_days)

        group_id = group_id or len(groups) + 1

        group, created = Group.objects.get_or_create(
            domain_or_id='test{}'.format(group_id),
            group_id=group_id,
            sex_last_update_date=week_ago,
            **kwargs
        )
        groups.append(group)
        return group

    yield _create_group


@pytest.fixture
def create_donor():
    donors = []

    def _create_donor(donor_id=None, **kwargs):
        donor_id = donor_id or len(donors) + 1

        donor, created = Donor.objects.get_or_create(
            id='test{}'.format(donor_id),
            **kwargs
        )
        donors.append(donor)
        return donor

    yield _create_donor


@pytest.fixture
def create_record():
    records = []

    def _create_record(group, donor, **kwargs):
        record_id = len(records) + 1

        group, created = Record.objects.get_or_create(
            donor=donor,
            group=group,
            record_id=record_id,
            **kwargs
        )
        records.append(group)
        return group

    yield _create_record
