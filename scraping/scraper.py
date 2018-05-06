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
        account_with_min_donors = min(accounts_with_donors, key=lambda x:len(x['donors']))
        for account in accounts_with_donors:
            if account['token'] == account_with_min_donors['token']:
                account['donors'].append(donor)

    return accounts_with_donors


def create_vk_api_using_service_token(token, api_version):
    return vk_requests.create_api(service_token=token, api_version=api_version)


def get_wall(api, id):
    # TODO обработка ошибок api
    if id.isdigit():
        wall = api.wall.get(owner_id='-{}'.format(id),
                            filter='owner',
                            api_version=VK_API_VERSION)
    else:
        wall = api.wall.get(domain=id,
                            filter='owner',
                            api_version=VK_API_VERSION)
    return wall


def filter_out_copies():
    pass


def filter_out_ads():
    pass


def filter_with_custom_filters():
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

            filter_with_custom_filters()

            # TODO добавление записей в бд


if __name__ == '__main__':
    main()