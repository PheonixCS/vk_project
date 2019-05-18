# Helpers to work with scraper data
from datetime import datetime, timedelta


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


def find_url_of_biggest_image(image_dict):
    photos_keys = [key for key in image_dict if key.startswith('photo_')]
    key_of_max_size_photo = max(photos_keys, key=lambda x: int(x.split('_')[1]))
    return image_dict[key_of_max_size_photo]


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
