# This command solve 152 task problem: parse

import logging
import re

from django.core.management.base import BaseCommand

from posting.models import Group
from scraping.models import Movie
from services.vk import core, videos

log = logging.getLogger('scraping.commands')


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
        pattern = r'(.*) \((\d\.\d).*\)'

        group = Group.objects.get(group_id=group_id)

        api = core.create_vk_session_using_login_password(
            group.user.login,
            group.user.password,
            group.user.app_id
        ).get_api()

        # TODO find in db these movies
        results = videos.get_all_group_videos(api, group_id)

        for video in results:
            try:
                vk_title, vk_rating = re.findall(pattern, video.get('title', '')).pop()
            except IndexError:
                log.warning('Index error', exc_info=True)
                continue

            db_movie = Movie.objects.get(title=vk_title, rating=vk_rating)
            if db_movie and db_movie.trailers.exists():
                first_trailer = db_movie.trailers.first()
                first_trailer.vk_url = f'video-{video.get("owner_id")}{video.get("id")}'
                log.debug('')
            else:
                log.warning(f'Movie {db_movie.title} has no trailer')
                continue
