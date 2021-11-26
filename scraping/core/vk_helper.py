# methods to work with vk api and data
import time


from django.db.models.query import QuerySet
from vk_requests.api import API

from services.vk.wall import get_records_info_from_groups
from services.vk.stat import fetch_liked_user_ids, get_users_sex_by_ids


def get_records_info(api: API, records: QuerySet) -> dict:
    posts = [f'-{record.donor.id}_{record.record_id}' for record in records]
    result = get_records_info_from_groups(api, posts)

    return result


# TODO need tests with mocks
def extract_records_sex(api: API, structured_records: dict) -> None:
    for donor in structured_records.keys():
        for record in structured_records[donor]:
            user_ids = fetch_liked_user_ids(api, donor, record['id'])
            sex_list = get_users_sex_by_ids(api, user_ids)

            if sex_list is None:
                pass

            unknown_count = sex_list.count(0)
            females_count = sex_list.count(1)
            males_count = sex_list.count(2)
            males_females_ratio = males_count / (females_count or 1)

            record.update(
                {'unknown_count': unknown_count,
                 'females_count': females_count,
                 'males_count': males_count,
                 'males_females_ratio': males_females_ratio}
            )
            time.sleep(1)
