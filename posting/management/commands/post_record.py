# custom command for posting
import logging
from datetime import datetime, timedelta

from constance import config
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from posting.core.poster import find_the_best_post
from posting.models import Group
from posting.tasks import (
    post_record,
    post_music,
    sex_statistics_weekly_task
)
from scraping.models import Record

log = logging.getLogger('posting.commands')


class Command(BaseCommand):
    help = 'Post record in specified groups'

    allowed_post_types = [
        'common',
        'music',
        'horoscope',
        'movie'
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '-g',
            '--group_id',
            type=int,
            help='id of the group',
            required=True
        )
        parser.add_argument(
            '-t',
            '--type',
            type=str,
            help='type of post',
            required=True
        )

    def handle(self, *args, **options):
        group_id = options['group_id']
        type_of_post = options['type']

        if type_of_post not in self.allowed_post_types:
            raise CommandError(f'Got not supported type of record! All supported: {self.allowed_post_types}')

        try:
            group = Group.objects.get(group_id=group_id)
        except Group.DoesNotExist:
            raise CommandError(f'Group {group_id} does not exist')

        now_time_utc = datetime.now(tz=timezone.utc)

        allowed_time_threshold = now_time_utc - timedelta(hours=8)
        week_ago = now_time_utc - timedelta(days=7)

        donors = group.donors.all()

        if len(donors) > 1:
            # find last record id and its donor id
            last_record = Record.objects.filter(group=group).order_by('-post_in_group_date').first()
            if last_record:
                donors = donors.exclude(pk=last_record.donor_id)

        records = [record for donor in donors for record in
                   donor.records.filter(rate__isnull=False,
                                        is_involved_now=False,
                                        post_in_group_date__isnull=True,
                                        failed_date__isnull=True,
                                        post_in_donor_date__gt=allowed_time_threshold)]

        if group.is_delete_audio_enabled:
            records = [record for record in records if
                       record.get_attachments_count() - record.audios.count() > 1]

        log.debug('got {} ready to post records to group {}'.format(len(records), group.group_id))
        if not records:
            self.stdout.write('Got no records')
            return

        if config.POSTING_BASED_ON_SEX:
            if not group.sex_last_update_date or group.sex_last_update_date < week_ago:
                sex_statistics_weekly_task.delay()
                self.stdout.write('Updating sex statistic')
                return

            if group.male_weekly_average_count == 0 or group.female_weekly_average_count == 0:
                group_male_female_ratio = 1
            else:
                group_male_female_ratio = group.male_weekly_average_count / group.female_weekly_average_count

            the_best_record = find_the_best_post(
                records,
                group_male_female_ratio,
                config.RECORDS_SELECTION_PERCENT
            )
        else:
            the_best_record = max(records, key=lambda x: x.rate)

        the_best_record.is_involved_now = True
        the_best_record.save(update_fields=['is_involved_now'])
        log.debug('record {} got max rate for group {}'.format(the_best_record, group.group_id))

        try:
            if group.is_background_abstraction_enabled:
                post_music.delay(group.user.login,
                                 group.user.password,
                                 group.user.app_id,
                                 group.group_id,
                                 the_best_record.id)
            else:
                post_record.delay(group.user.login,
                                  group.user.password,
                                  group.user.app_id,
                                  group.group_id,
                                  the_best_record.id)
        except:
            log.error('got unexpected exception in examine_groups', exc_info=True)
            the_best_record.is_involved_now = False
            the_best_record.save(update_fields=['is_involved_now'])

        self.stdout.write(f'Successfully post in group {group_id}')
