# Temporary vk helper module for posting

import logging
from datetime import datetime

from django.utils import timezone

from posting.models import AdRecord
from services.vk.wall import get_ad_in_last_hour
from services.vk.core import create_vk_session_using_login_password

log = logging.getLogger('posting.core.vk_helper')


def is_ads_posted_recently(group):
    session = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id)
    if not session:
        return False
    api = session.get_api()
    if not api:
        # if we got no api here, we still can continue posting
        return False
    if api:
        ad_record = get_ad_in_last_hour(api, group.domain_or_id)
        if ad_record:
            AdRecord.objects.get_or_create(ad_record_id=ad_record['id'],
                                           group=group,
                                           post_in_group_date=datetime.fromtimestamp(ad_record['date'],
                                                                                     tz=timezone.utc))
            return True
