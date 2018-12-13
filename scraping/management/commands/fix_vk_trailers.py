# This command solve 152 task problem: parse

from django.core.management.base import BaseCommand
from services.vk import core, videos
from posting.models import Group


class Command(BaseCommand):
    help = 'fix trailers that was uploaded in vk but got no vk_url'

    def add_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--group_id',
            type=int,
            default=27045802,
            help='id of the group'
        )

    def handle(self, *args, **options):
        group_id = options['group_id']

        group = Group.objects.get(group_id=group_id)

        api = core.create_vk_session_using_login_password(
            group.user.login,
            group.user.password,
            group.user.app_id
        ).get_api()

        results = videos.get_all_group_videos(api, group_id)
