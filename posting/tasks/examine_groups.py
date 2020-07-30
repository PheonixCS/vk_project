import logging
from datetime import timedelta
from random import choice

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

    log.debug('got {} groups'.format(len(groups_to_post_in)))

    now_time_utc = timezone.now()
    now_minute = now_time_utc.minute
    now_hour = now_time_utc.hour

    ads_time_threshold = now_time_utc - timedelta(hours=1, minutes=5)
    hour_ago_threshold = now_time_utc - timedelta(hours=1)
    allowed_time_threshold = now_time_utc - timedelta(hours=8)
    week_ago = now_time_utc - timedelta(days=7)

    for group in groups_to_post_in:
        log.debug('working with group {}'.format(group.domain_or_id))

        last_hour_ads = AdRecord.objects.filter(group=group, post_in_group_date__gt=ads_time_threshold)
        if last_hour_ads.exists():
            log.debug(f'got ads in last hour and 5 minutes for group {group.domain_or_id}. Skip.')
            continue

        if group.is_horoscopes and group.horoscopes.filter(post_in_group_date__isnull=True):
            # https://trello.com/c/uB0RQBvE/244
            # в мужских гороскопах нужно постить на минуту позже.
            if group.group_id == 29062628:
                now_minute -= 1

            is_time_to_post = abs(now_minute - group.posting_time.minute) % config.HOROSCOPES_POSTING_INTERVAL == 0
        else:
            is_time_to_post = group.posting_time.minute == now_minute

        # https://trello.com/c/uB0RQBvE/244
        # https://trello.com/c/uA5o3XuR/247
        # if group.group_type == Group.HOROSCOPES_COMMON:
        #     hour_ago_threshold -= timedelta(hours=1)
        #     if is_time_to_post and now_time_utc.hour % 2 == 0:
        #         log.debug('Horoscopes time to post')
        #         is_time_to_post = True
        #     else:
        #         log.debug('Not horoscopes time to post')
        #         is_time_to_post = False

        # https://trello.com/c/uB0RQBvE/248
        if config.NEW_POSTING_INTERVALS_ENABLE and group.group_type == Group.HOROSCOPES_COMMON:
            is_time_to_post = (now_hour, now_minute) in group.return_posting_time_list()
            hour_ago_threshold = now_time_utc - timedelta(minutes=group.posting_interval)
            log.info(
                f'Now time: {is_time_to_post}{hour_ago_threshold}\n'
                f'is_time_to_post {is_time_to_post}\n',
                f'hour_ago_threshold {hour_ago_threshold}'
            )

        if group.is_movies:
            last_hour_movies = Movie.objects.filter(post_in_group_date__gt=hour_ago_threshold)
            movies_exist = last_hour_movies.exists()
        else:
            movies_exist = False

        if group.is_horoscopes:
            last_hour_horoscopes = Horoscope.objects.filter(group=group, post_in_group_date__gt=hour_ago_threshold)
            horoscopes_exist = last_hour_horoscopes.exists()
        else:
            horoscopes_exist = False

        last_hour_posts_common = Record.objects.filter(group=group, post_in_group_date__gt=hour_ago_threshold)

        last_hour_posts_exist = last_hour_posts_common.exists() or movies_exist or horoscopes_exist

        if last_hour_posts_exist and not is_time_to_post:
            log.info(f'got posts in last hour and 5 minutes for group {group.domain_or_id}')
            continue
        else:
            if not config.IS_DEV and is_ads_posted_recently(group):
                log.info(f'pass group {group.domain_or_id} because ad post was published recently')
                continue

        if not group.group_id:
            session = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id)
            if not session:
                continue
            api = session.get_api()
            if not api:
                continue
            group.group_id = fetch_group_id(api, group.domain_or_id)
            group.save(update_fields=['group_id'])

        movies_condition = (
                group.is_movies
                and (is_time_to_post or not last_hour_posts_exist or config.FORCE_MOVIE_POST)
        )
        if movies_condition:
            log.debug(f'{group.domain_or_id} in movies condition')

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

            if movie:
                post_movie.post_movie.delay(group.group_id, movie)
            else:
                log.warning('got no movie')

        horoscope_condition = (
                group.is_horoscopes
                and is_time_to_post
                and group.horoscopes.filter(post_in_group_date__isnull=True)
        )
        if horoscope_condition:
            log.debug(f'{group.domain_or_id} in horoscopes condition')

            horoscope_records = group.horoscopes.filter(post_in_group_date__isnull=True)
            if horoscope_records.exists():

                horoscope_signs = HoroscopesPage.get_signs()
                for sign in horoscope_signs:
                    records_filter = horoscope_records.filter(zodiac_sign=sign)
                    if records_filter:
                        horoscope_record = records_filter.last()
                        break
                else:
                    horoscope_record = horoscope_records.last()

                post_horoscope.post_horoscope.delay(group.user.login,
                                                    group.user.password,
                                                    group.user.app_id,
                                                    group.group_id,
                                                    horoscope_record.id
                                                    )
                continue
            else:
                log.warning('got no horoscopes records')

        common_condition = (
                (is_time_to_post or not last_hour_posts_exist)
                and not group.is_movies
        )
        if common_condition:
            log.debug(f'{group.domain_or_id} in common condition')

            donors = group.donors.all()
            if not donors:
                log.warning(f'Group {group.domain_or_id} got no donors but in common condition!')
                continue

            if len(donors) > 1:
                # find last record id and its donor id
                last_record = Record.objects.filter(group=group).order_by('-post_in_group_date').first()
                if last_record:
                    donors = donors.exclude(pk=last_record.donor_id)

            records = Record.objects.filter(
                rate__isnull=False,
                status=Record.READY,
                post_in_group_date__isnull=True,
                failed_date__isnull=True,
                post_in_donor_date__gt=allowed_time_threshold,
                donor__in=donors
            )

            if group.banned_origin_attachment_types:
                records = filter_banned_records(records, group.banned_origin_attachment_types)

            log.debug('got {} ready to post records to group {}'.format(len(records), group.group_id))
            if not records:
                continue

            if config.POSTING_BASED_ON_SEX:
                if (
                        group.group_type not in (Group.MUSIC_COMMON,)
                        and (not group.sex_last_update_date or group.sex_last_update_date < week_ago)
                ):
                    sex_statistics_weekly.delay()
                    continue

                male_percent, female_percent = group.get_auditory_percents()

                the_best_record = find_suitable_record(
                    records,
                    (male_percent, female_percent),
                    config.RECORDS_SELECTION_PERCENT,
                    group.group_id
                )
            else:
                the_best_record = max(records, key=lambda x: x.rate)

            the_best_record.status = Record.POSTING
            the_best_record.save(update_fields=['status'])
            log.debug('record {} got max rate for group {}'.format(the_best_record, group.group_id))

            save_posting_history(group=group, record=the_best_record, candidates=records.exclude(pk=the_best_record.id))

            try:
                if group.is_background_abstraction_enabled:
                    post_music.post_music.delay(group.user.login,
                                                group.user.password,
                                                group.user.app_id,
                                                group.group_id,
                                                the_best_record.id)
                else:
                    post_record.post_record.delay(group.user.login,
                                                  group.user.password,
                                                  group.user.app_id,
                                                  group.group_id,
                                                  the_best_record.id)
            except:
                log.error('got unexpected exception in examine_groups', exc_info=True)
                telegram.critical('Неожиданная ошибка при подготовке к постингу')
                the_best_record.status = Record.FAILED
                the_best_record.save(update_fields=['status'])

    log.debug('end group examination')
    return 'succeed'
