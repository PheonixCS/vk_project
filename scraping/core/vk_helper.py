# methods to work with vk api and data

from django.db.models.query import QuerySet
from services.vk.wall import get_records_info_from_groups
from vk_requests.api import API


def get_records_info(api: API, records: QuerySet) -> dict:

    posts = [f'-{record.donor.id}_{record.record_id}' for record in records]
    result = get_records_info_from_groups(api, posts)

    return result
