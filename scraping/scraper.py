import vk_requests

from posting.models import User
from scraping.models import Donor
from settings.models import Setting

VK_API_VERSION = Setting.get_value(key='VK_API_VERSION')


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


def create_vk_api_using_service_token(token, api_version):
    return vk_requests.create_api(service_token=token, api_version=api_version)


def get_wall(api, group_id):
    # TODO обработка ошибок api
    if group_id.isdigit():
        wall = api.wall.get(owner_id='-{}'.format(group_id),
                            filter='owner',
                            api_version=VK_API_VERSION)
    else:
        wall = api.wall.get(domain=group_id,
                            filter='owner',
                            api_version=VK_API_VERSION)
    return wall


def filter_out_copies():
    pass


def filter_out_ads():
    pass


def filter_with_custom_filters(custom_filters, records):
    for custom_filter in custom_filters:
        for record in records:
            if custom_filter.min_quantity_of_line_breaks:
                if len(record['text'].splitlines()) < custom_filter.min_quantity_of_line_breaks:
                    records.remove(record)
                    continue

            if custom_filter.min_text_length:
                if len(record['text']) < custom_filter.min_text_length:
                    records.remove(record)
                    continue

            if custom_filter.min_quantity_of_videos:
                number_of_videos = len([item for item in record['attachments'] if item['type'] == 'video'])
                if number_of_videos < custom_filter.min_quantity_of_videos:
                    records.remove(record)
                    continue

            if custom_filter.min_quantity_of_images:
                number_of_images = len([item for item in record['attachments'] if item['type'] == 'photo'])
                if number_of_images < custom_filter.min_quantity_of_images:
                    records.remove(record)
                    continue

            if custom_filter.min_quantity_of_gifs:
                number_of_gifs = len([item for item in record['attachments'] if item['type'] == 'doc' and
                                                                                item['doc']['ext'] == 'gif'])
                if number_of_gifs < custom_filter.min_quantity_of_gifs:
                    records.remove(record)
                    continue
    return records


def save_record_to_db(donor, record):
    pass


def main():
    tokens = [acc.app_service_token for acc in User.objects.filter(app_service_token__isnull=False, group=None)]
    donors = Donor.objects.filter(is_involved=True)

    accounts_with_donors = distribute_donors_between_accounts(donors, tokens)

    for account in accounts_with_donors:
        if not account['donors']:
            continue

        api = create_vk_api_using_service_token(account['token'], VK_API_VERSION)

        for donor in account['donors']:
            records = get_wall(api, donor.id)['items']

            filter_out_copies()

            filter_out_ads()

            custom_filters = donor.filters.all()
            if custom_filters:
                records = filter_with_custom_filters(custom_filters, records)

            for record in records:
                save_record_to_db(donor, record)


if __name__ == '__main__':
    main()
