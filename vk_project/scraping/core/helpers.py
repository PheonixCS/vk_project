# Helpers to work with scraper data
from datetime import date, datetime, timedelta
from constance import config
from typing import List


def find_newest_record(records: List[dict]) -> dict:
    return max(records, key=lambda x: x.get('date', 0) if not x.get('is_pinned') else 0) if records else {}


def is_donor_out_of_date(newest_record_date: int, date_to_compare: date = date.today(), outdate_interval: int = None) \
        -> bool:
    outdate_interval = outdate_interval or config.DONOR_OUTDATE_INTERVAL
    return date_to_compare - date.fromtimestamp(newest_record_date) > timedelta(days=outdate_interval)


def distribute_donors_between_accounts(donors, accounts):
    accounts_with_donors = [{
        'token': token,
        'donors': []
    } for token in accounts]

    for donor in donors:
        account_with_min_donors = min(accounts_with_donors, key=lambda x: len(x['donors']))
        for account in accounts_with_donors:
            if account['token'] == account_with_min_donors['token']:
                account['donors'].append(donor)

    return accounts_with_donors


# old for version below 5.77
# def find_url_of_biggest_image(image_dict: dict) -> str:
#     photos_keys = [key for key in image_dict if key.startswith('photo_')]
#     key_of_max_size_photo = max(photos_keys, key=lambda x: int(x.split('_')[1]))
#     return image_dict[key_of_max_size_photo]

# for API version 5.77+
# https://vk.com/dev/photo_sizes
# https://vk.com/dev/objects/photo
def find_url_of_biggest_image(image_dict: dict) -> str:
    result = ''

    sizes = image_dict.get('sizes', [])
    if sizes:
        result = max(sizes, key=lambda x: x['width'])
        result = result['url']

    return result


def extract_records_per_donor(vk_response: dict) -> dict:
    """
    We got response from vk as list of records from different groups.
    Need map groups to list of its records
    """
    group_records_map = dict()

    group_ids = [group_id.get('id') for group_id in vk_response.get('groups', [])]

    for group_id in group_ids:
        current_group = {group_id: [record for record in vk_response.get('items')
                                    if record.get('owner_id') == -group_id]}
        group_records_map.update(current_group)

    return group_records_map


def get_tomorrow_date_ru():
    tomorrow = datetime.now() + timedelta(days=1)

    month_ru = [
        'января',
        'февраля',
        'марта',
        'апреля',
        'мая',
        'июня',
        'июля',
        'августа',
        'сентября',
        'октября',
        'ноября',
        'декабря'
    ]

    date = '{} {}'.format(tomorrow.day, month_ru[int(tomorrow.strftime('%m')) - 1])

    return date
