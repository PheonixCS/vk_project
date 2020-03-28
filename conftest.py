import pytest


@pytest.fixture(autouse=True, scope='session')
def enable_db_access_for_all_tests(transactional_db):
    pass
