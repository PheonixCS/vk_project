#


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
