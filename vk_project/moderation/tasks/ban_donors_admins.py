import logging

from celery import shared_task

from moderation.core.vk_helpers import get_groups_by_id, ban_user
from posting.models import Group
from services.vk.core import create_vk_session_using_login_password

log = logging.getLogger('moderation.tasks')


@shared_task(time_limit=5)
def ban_donors_admins():
    log.info('start ban_donors_admins task')

    active_groups = Group.objects.filter(
        user__isnull=False,
        is_posting_active=True).distinct()

    for group in active_groups:
        donors_ids = [donor.id for donor in group.donors.all()]
        log.info(f'working with group {group.domain_or_id} donors {donors_ids}')

        session = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id)
        api = session.get_api()
        if not api:
            log.warning(f'group {group.domain_or_id} no api created!')
            return None

        donors = get_groups_by_id(api, donors_ids, fields='contacts')

        for donor in donors:
            for contact in donor.get('contacts', []):
                if contact.get('user_id'):
                    log.info(f'ban user {contact["user_id"]} in group {group.domain_or_id} : '
                             f'is admin in donor {donor.get("id")}')
                    ban_user(api, group.group_id, contact['user_id'],
                             comment=f'Администратор в источнике {donor.get("id")}')

    log.info('ban_donors_admins task completed')
