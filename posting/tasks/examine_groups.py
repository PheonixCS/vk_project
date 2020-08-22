import logging
from datetime import timedelta
from random import choice
from typing import List, Tuple

from celery import shared_task
from constance import config
from django.utils import timezone

from posting.core.poster import get_movies_rating_intervals, get_next_interval_by_movie_rating, filter_banned_records, \
    find_suitable_record
from posting.core.posting_history import save_posting_history
from posting.core.vk_helper import is_ads_posted_recently
from posting.models import Group, AdRecord
from posting.tasks import post_movie, post_horoscope, sex_statistics_weekly, post_music, post_record
from scraping.models import Movie, Horoscope, Record, Trailer
from services.horoscopes.core import HoroscopesPage
from services.vk.core import create_vk_session_using_login_password, fetch_group_id

log = logging.getLogger('posting.scheduled')
telegram = logging.getLogger('telegram')


@shared_task(time_limit=59)
def examine_groups():
    log.debug('start group examination')
    groups_to_post_in = Group.objects.filter(
        user__isnull=False,
        is_posting_active=True
    ).distinct()
    log.debug(f'Got {len(groups_to_post_in)} groups')

    for group in groups_to_post_in:
        log.debug(f'Working with group {group.domain_or_id}')

        ads = are_any_ads_posted_recently(group)
        if ads:
            log.info(f'Got recent ads in group {group.domain_or_id}. Skip posting.')
            continue

        is_time_to_post, last_hour_posts_exist = is_it_time_to_post(group)
        if last_hour_posts_exist and not is_time_to_post:
            log.info(f'Got recent posts in group {group.domain_or_id}. Skip posting.')
            continue

        # FIXME move this group id stuff somewhere
        if not group.group_id:
            group_id = fetch_group_id_from_vk(group)
            if not group_id:
                continue

        movies_condition = (
                group.group_type == group.MOVIE_SPECIAL
                and (is_time_to_post or not last_hour_posts_exist or config.FORCE_MOVIE_POST)
        )
        if movies_condition:
            log.debug(f'{group.domain_or_id} in movies condition')

            movie = find_movie_id_to_post()
            if movie:
                post_movie.post_movie.delay(group.group_id, movie)
            else:
                log.warning('Got no movie to post')

            continue

        horoscope_condition = (
                group.group_type in (Group.HOROSCOPES_MAIN, Group.HOROSCOPES_COMMON)
                and is_time_to_post
                and group.horoscopes.filter(post_in_group_date__isnull=True)
        )
        if horoscope_condition:
            log.debug(f'{group.domain_or_id} in horoscopes condition')

            horoscope_record = find_horoscope_record_to_post(group)
            if horoscope_record:
                post_horoscope.post_horoscope.delay(group.group_id, horoscope_record.id)
            else:
                log.warning('Got no horoscope records to post')

            continue

        common_condition = (
                (is_time_to_post or not last_hour_posts_exist)
                and not group.group_type == Group.MOVIE_SPECIAL
        )
        if common_condition:
            log.debug(f'{group.domain_or_id} in common condition')

            the_best_record, records = find_common_record_to_post(group)
            if the_best_record:
                the_best_record.set_posting()
                log.debug(f'record {the_best_record} got max rate for group {group.group_id}')

                save_posting_history(group=group, record=the_best_record,
                                     candidates=records.exclude(pk=the_best_record.id))

                try:
                    if group.is_background_abstraction_enabled:
                        post_music.post_music.delay(group.group_id, the_best_record.id)
                    else:
                        post_record.post_record.delay(group.group_id, the_best_record.id)
                except:
                    log.error('got unexpected exception in examine_groups', exc_info=True)
                    telegram.critical('Неожиданная ошибка при подготовке к постингу')
                    the_best_record.set_failed()

            continue

        log.warning(f'Group {group.group_id} did not meet any of the posting condition!')

    log.debug('end group examination')
    return 'succeed'


def is_it_time_to_post(group: Group) -> Tuple[bool, bool]:
    now_time_utc = timezone.now()
    now_minute = now_time_utc.minute
    now_hour = now_time_utc.hour

    # https://trello.com/c/uB0RQBvE/248
    is_time_to_post = (now_hour, now_minute) in group.return_posting_time_list()
    posting_pause_threshold = now_time_utc - timedelta(minutes=group.posting_interval)
    log.debug(f'is_time_to_post: {is_time_to_post}, posting_pause_threshold: {posting_pause_threshold}')

    # https://trello.com/c/uB0RQBvE/244
    if group.group_type == Group.HOROSCOPES_MAIN and group.horoscopes.filter(post_in_group_date__isnull=True):
        # в мужских гороскопах нужно постить на минуту позже.
        if group.group_id == 29062628:
            now_minute -= 1

        interval = config.HOROSCOPES_POSTING_INTERVAL - 1
        is_time_to_post = (now_hour, now_minute) in group.return_posting_time_list(interval=interval)
        posting_pause_threshold = now_time_utc - timedelta(minutes=interval)

    if group.group_type == group.MOVIE_SPECIAL:
        last_hour_movies = Movie.objects.filter(post_in_group_date__gt=posting_pause_threshold)
        movies_exist = last_hour_movies.exists()
    else:
        movies_exist = False

    if group.group_type in (Group.HOROSCOPES_COMMON, Group.HOROSCOPES_MAIN):
        last_hour_horoscopes = Horoscope.objects.filter(group=group, post_in_group_date__gt=posting_pause_threshold)
        horoscopes_exist = last_hour_horoscopes.exists()
    else:
        horoscopes_exist = False

    last_hour_posts_common = Record.objects.filter(group=group, post_in_group_date__gt=posting_pause_threshold)
    last_hour_posts_exist = last_hour_posts_common.exists() or movies_exist or horoscopes_exist

    return is_time_to_post, last_hour_posts_exist


def fetch_group_id_from_vk(group: Group) -> int or None:
    session = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id)
    if not session:
        return None

    api = session.get_api()
    if not api:
        return None

    group_id = fetch_group_id(api, group.domain_or_id)
    group.group_id = group_id
    group.save(update_fields=['group_id'])

    return group_id


def find_common_record_to_post(group: Group) -> Tuple[Record or None, List[Record] or None]:
    now_time_utc = timezone.now()
    week_ago = now_time_utc - timedelta(days=7)
    allowed_time_threshold = now_time_utc - timedelta(hours=8)

    donors = group.donors.all()
    if not donors:
        log.warning(f'Group {group.domain_or_id} got no donors but in common condition!')
        return None, []

    if len(donors) > 1:
        # find last record id and its donor id
        last_record = Record.objects.filter(group=group).order_by('-post_in_group_date').first()
        if last_record:
            donors = donors.exclude(pk=last_record.donor_id)

    candidates = Record.objects.filter(
        rate__isnull=False,
        status=Record.READY,
        post_in_group_date__isnull=True,
        failed_date__isnull=True,
        post_in_donor_date__gt=allowed_time_threshold,
        donor__in=donors
    )

    if group.banned_origin_attachment_types:
        candidates = filter_banned_records(candidates, list(group.banned_origin_attachment_types))

    log.debug(f'got {len(candidates)} ready to post records to group {group.group_id}')
    if not candidates:
        return None, []

    if config.POSTING_BASED_ON_SEX:
        if (
                group.group_type not in (Group.MUSIC_COMMON,)
                and (not group.sex_last_update_date or group.sex_last_update_date < week_ago)
        ):
            sex_statistics_weekly.delay()
            return None, []

        male_percent, female_percent = group.get_auditory_percents()

        the_best_record = find_suitable_record(
            candidates,
            (male_percent, female_percent),
            config.RECORDS_SELECTION_PERCENT,
            group.group_id
        )
    else:
        the_best_record = max(candidates, key=lambda x: x.rate)

    return the_best_record, candidates


def find_horoscope_record_to_post(group: Group) -> Horoscope or None:
    horoscope_records = group.horoscopes.filter(post_in_group_date__isnull=True)
    horoscope_record = None

    if horoscope_records.exists():

        horoscope_signs = HoroscopesPage.get_signs()
        for sign in horoscope_signs:
            records_filter = horoscope_records.filter(zodiac_sign=sign)
            if records_filter:
                horoscope_record = records_filter.last()
                break
        else:
            horoscope_record = horoscope_records.last()
    return horoscope_record


def find_movie_id_to_post() -> int or None:
    now_time_utc = timezone.now()
    posted_movies = Movie.objects.filter(post_in_group_date__isnull=False)

    if posted_movies:
        last_posted_movie = posted_movies.latest('post_in_group_date')
        last_movie_rating = last_posted_movie.rating
        log.debug(f'last posted movie id: {last_posted_movie.id or None}')
    else:
        log.warning('got no posted movies')
        last_movie_rating = None

    for _ in range(len(get_movies_rating_intervals())):
        next_rating_interval = get_next_interval_by_movie_rating(last_movie_rating)
        log.debug(f'next rating interval {next_rating_interval}')

        new_movie = Movie.objects.filter(trailers__status=Trailer.DOWNLOADED_STATUS,
                                         rating__in=next_rating_interval,
                                         post_in_group_date__isnull=True).last()
        if not new_movie:
            log.debug('Got no new movie')
            old_movie_threshold = now_time_utc - timedelta(days=config.OLD_MOVIES_TIME_THRESHOLD)
            old_movies_ids = list(Movie.objects.filter(
                trailers__vk_url__isnull=False,
                post_in_group_date__lte=old_movie_threshold,
                rating__in=next_rating_interval
            ).values_list('id', flat=True))

            try:
                old_movie = choice(old_movies_ids)
            except IndexError:
                log.debug('old_movies_ids is empty')
                old_movie = None

            if not old_movie:
                log.warning('Got no movies in last interval!')
            else:
                log.debug('Found old movie')
                movie = old_movie
                break
        else:
            log.debug('Found new movie')
            movie = new_movie.id
            break

        last_movie_rating = next_rating_interval[0]

    else:
        movie = None
    return movie


def are_any_ads_posted_recently(group: Group) -> bool:
    now_time_utc = timezone.now()
    ads_time_threshold = now_time_utc - timedelta(hours=1, minutes=5)

    result = False

    last_hour_ads = AdRecord.objects.filter(group=group, post_in_group_date__gt=ads_time_threshold)
    if last_hour_ads.exists():
        return result

    if not config.IS_DEV and is_ads_posted_recently(group):
        return result

    return result
