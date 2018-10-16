# Temporary vk helper module for posting

import logging
from datetime import datetime

from django.utils import timezone

from posting.models import AdRecord
from posting.poster import create_vk_session_using_login_password, get_ad_in_last_hour

log = logging.getLogger('posting.core.vk_helper')


def is_ads_posted_recently(group):
    api = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id).get_api()
    if api:
        ad_record = get_ad_in_last_hour(api, group.domain_or_id)
        if ad_record:
            AdRecord.objects.create(ad_record_id=ad_record['id'],
                                    group=group,
                                    post_in_group_date=datetime.fromtimestamp(ad_record['date'],
                                                                              tz=timezone.utc))
            log.info('pass group {} due to ad in last hour'.format(group.domain_or_id))
            return True
    if not api:
        # if we got no api here, we still can continue posting
        return False
