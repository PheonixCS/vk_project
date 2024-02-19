import logging

from celery import shared_task
from django.utils import timezone

from posting.core.poster import get_groups_to_update_sex_statistics
from services.vk.stat import get_group_week_statistics

log = logging.getLogger('posting.scheduled')


@shared_task(time_limit=180, name='posting.tasks.sex_statistics_weekly.sex_statistics_weekly')
def sex_statistics_weekly():
    log.debug('sex_statistics_weekly started')

    # TODO сделал временно
    log.debug('exit sex_statistics_weekly, enable it later')
    return

    groups = get_groups_to_update_sex_statistics()

    for group in groups:
        session = create_vk_session_with_access_token(group.user)
        if not session:
            continue

        api = session.get_api()
        if not api:
            continue

        stats = get_group_week_statistics(api, group_id=group.group_id)

        male_count_list = []
        female_count_list = []

        for day in stats:
            reach = day.get('reach')
            sex_list = reach.get('sex', [])
            for sex in sex_list:
                if sex.get('value', 'n') == 'f':
                    female_count_list.append(sex.get('count'))
                elif sex.get('value', 'n') == 'm':
                    male_count_list.append(sex.get('count'))

        if male_count_list:
            male_average_count = sum(male_count_list) // len(male_count_list)
        else:
            male_average_count = 0

        if female_count_list:
            female_average_count = sum(female_count_list) // len(female_count_list)
        else:
            female_average_count = 0

        group.male_weekly_average_count = male_average_count
        group.female_weekly_average_count = female_average_count
        group.sex_last_update_date = timezone.now()

        group.save(update_fields=['male_weekly_average_count', 'female_weekly_average_count', 'sex_last_update_date'])

    log.debug('sex_statistics_weekly finished')
