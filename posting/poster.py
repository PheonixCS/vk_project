import datetime

import vk_requests
from vk_requests.exceptions import VkAPIError
from django.db.models import Max
import logging

from posting.models import Group
from settings.models import Setting

log = logging.getLogger('posting.poster')

VK_API_VERSION = Setting.get_value(key='VK_API_VERSION')


def create_vk_api_using_login_password(login, password):
    log.debug('create api called')

    try:
        api = vk_requests.create_api(login=login, password=password, api_version=VK_API_VERSION)
    except VkAPIError as error_msg:
        log.info('User {} got api error: {}'.format(login, error_msg))
        return None

    return api


def post_record(api, group_id, record):
    try:
        # TODO api постинг
        pass
    except VkAPIError as error_msg:
        log.info('group {} got api error: {}'.format(group_id, error_msg))
        return False

    return True


def main():
    log.info('start main scrapper')
    groups_to_post_in = Group.objects.filter(user__isnull=False, donors__isnull=False)

    for group in groups_to_post_in:
        log.debug('working with group {}'.format(group.id))

        api = create_vk_api_using_login_password(group.user.login, group.user.password)
        if not api:
            continue

        # TODO условие: time_now_minute = posting_time_minute
        if True:
            records = [record for donor in group.donors.all() for record in
                       donor.records.filter(rate__isnull=False, post_in_group_date__isnull=True)]
            log.debug('got {} ready to post records'.format(len(records)))

            record_with_max_rate = max(records, key=lambda x:x.rate)
            log.debug('record {} got max rate'.format(record_with_max_rate))

            response = post_record(api, group.id, record_with_max_rate)

            if response:
                record_with_max_rate.post_in_group_date = datetime.datetime.now()
                record_with_max_rate.save(update_fields=['post_in_group_date'])


if __name__ == '__main__':
    main()
