import logging
from datetime import datetime, timedelta
from random import choice, shuffle

import vk_api
from celery import task
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from constance import config

from posting.models import Group, ServiceToken, AdRecord
from posting.poster import (
    create_vk_session_using_login_password,
    fetch_group_id,
    upload_photo,
    delete_hashtags_from_text,
    get_ad_in_last_hour,
    check_docs_availability,
    check_video_availability,
    delete_emoji_from_text,
    download_file,
    prepare_image_for_posting,
    merge_six_images_into_one,
    is_images_size_nearly_the_same,
    is_text_on_image,
    is_all_images_vertical,
    delete_files,
    get_group_week_statistics,
    find_the_best_post
)
from scraping.core.vk_helper import get_wall, create_vk_api_using_service_token
from scraping.models import Record, Horoscope
from posting.text_utilities import replace_russian_with_english_letters

log = logging.getLogger('posting.scheduled')


@task
def examine_groups():
    log.debug('start group examination')
    groups_to_post_in = Group.objects.filter(user__isnull=False,
                                             donors__isnull=False,
                                             is_posting_active=True).distinct()

    log.debug('got {} groups'.format(len(groups_to_post_in)))

    now_time = datetime.now(tz=timezone.utc)
    now_minute = now_time.minute

    time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=1, minutes=5)
    allowed_time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=8)
    week_ago = datetime.now(tz=timezone.utc) timedelta(days=7)
    today_start = now_time.replace(hour=0, minute=0, second=0)

    for group in groups_to_post_in:
        log.debug('working with group {}'.format(group.domain_or_id))

        if not group.group_id:
            api = create_vk_session_using_login_password(group.user.login,
                                                         group.user.password,
                                                         group.user.app_id).get_api()
            if not api:
                continue
            group.group_id = fetch_group_id(api, group.domain_or_id)
            group.save(update_fields=['group_id'])

        log.debug('start searching for posted records since {}'.format(time_threshold))
        last_hour_posts_count = Record.objects.filter(group=group, post_in_group_date__gt=time_threshold).count()
        log.debug('got {} posts in last hour and 5 minutes'.format(last_hour_posts_count))

        log.debug('start searching for ads in last hour and 5 minutes')
        last_hour_ads_count = AdRecord.objects.filter(group=group, post_in_group_date__gt=time_threshold).count()
        log.debug('got {} ads in last hour and 5 minutes'.format(last_hour_ads_count))

        horoscope_posting_interval = 3
        if group.is_horoscopes and group.horoscopes.filter(post_in_group_date__isnull=True) \
                and abs(now_minute - group.posting_time.minute) % horoscope_posting_interval == 0 \
                and not last_hour_ads_count:
            api = create_vk_session_using_login_password(group.user.login,
                                                         group.user.password,
                                                         group.user.app_id).get_api()
            if api:
                ad_record = get_ad_in_last_hour(api, group.domain_or_id)
                if ad_record:
                    try:
                        AdRecord.objects.create(ad_record_id=ad_record['id'],
                                                group=group,
                                                post_in_group_date=datetime.fromtimestamp(ad_record['date'],
                                                                                          tz=timezone.utc))
                        log.info('pass group {} due to ad in last hour'.format(group.domain_or_id))
                        continue
                    except:
                        log.error('got unexpected error', exc_info=True)
            if not api:
                # if we got no api here, we still can continue posting
                pass

            try:
                horoscope_record_id = group.horoscopes.filter(post_in_group_date__isnull=True,
                                                              post_in_donor_date__gt=today_start).last().id
                if horoscope_record_id:
                    post_horoscope.delay(group.user.login,
                                         group.user.password,
                                         group.user.app_id,
                                         group.group_id,
                                         horoscope_record_id)
                    continue
                else:
                    log.warning('got no horoscopes records')
            except:
                log.error('got unexpected exception in examine_groups', exc_info=True)

        if (group.posting_time.minute == now_minute or not last_hour_posts_count) and not last_hour_ads_count:

            api = create_vk_session_using_login_password(group.user.login,
                                                         group.user.password,
                                                         group.user.app_id).get_api()
            if api:
                ad_record = get_ad_in_last_hour(api, group.domain_or_id)
                if ad_record:
                    try:
                        AdRecord.objects.create(ad_record_id=ad_record['id'],
                                                group=group,
                                                post_in_group_date=datetime.fromtimestamp(ad_record['date'],
                                                                                          tz=timezone.utc))
                        log.info('pass group {} due to ad in last hour'.format(group.domain_or_id))
                        continue
                    except:
                        log.error('got unexpected error', exc_info=True)
            if not api:
                # if we got no api here, we still can continue posting
                pass

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
            log.debug('got {} ready to post records to group {}'.format(len(records), group.group_id))
            if not records:
                continue

            if config.POSTING_BASED_ON_SEX:

                if group.sex_last_update_date < week_ago:
                    sex_statistics_weekly.delay()
                    break

                group_male_female_ratio = group.male_weekly_average_count/group.female_weekly_average_count
                the_best_record = find_the_best_post(records, group_male_female_ratio)
            else:
                the_best_record = max(records, key=lambda x: x.rate)

            the_best_record.is_involved_now = True
            the_best_record.save(update_fields=['is_involved_now'])
            log.debug('record {} got max rate for group {}'.format(the_best_record, group.group_id))

            try:
                post_record.delay(group.user.login,
                                  group.user.password,
                                  group.user.app_id,
                                  group.group_id,
                                  the_best_record.id)
            except:
                log.error('got unexpected exception in examine_groups', exc_info=True)
                the_best_record.is_involved_now = False
                the_best_record.save(update_fields=['is_involved_now'])


@task
def post_horoscope(login, password, app_id, group_id, horoscope_record_id):
    log.debug('start posting horoscopes in {} group'.format(group_id))

    session = create_vk_session_using_login_password(login, password, app_id)
    api = session.get_api()

    if not session:
        log.error('session not created in group {}'.format(group_id))
        return

    if not api:
        log.error('no api was created in group {}'.format(group_id))
        return

    group = Group.objects.get(group_id=group_id)
    horoscope_record = group.horoscopes.get(pk=horoscope_record_id)
    log.debug('{} horoscope record to post in {}'.format(horoscope_record.id, group.domain_or_id))

    try:
        attachments = []

        record_text = horoscope_record.text
        record_text = delete_hashtags_from_text(record_text)

        if horoscope_record.image_url:
            image_local_filename = download_file(horoscope_record.image_url)
            attachments = upload_photo(session, image_local_filename, group_id)

        post_response = api.wall.post(owner_id='-{}'.format(group_id),
                                      from_group=1,
                                      message=record_text,
                                      attachments=attachments)
        log.debug('{} in group {}'.format(post_response, group_id))
    except vk_api.VkApiError as error_msg:
        log.info('group {} got api error: {}'.format(group_id, error_msg))
        return
    except:
        log.error('caught unexpected exception in group {}'.format(group_id), exc_info=True)
        return

    horoscope_record.post_in_group_date = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    horoscope_record.save()
    log.debug('post horoscopes in group {} finished'.format(group_id))


@task
def post_record(login, password, app_id, group_id, record_id):
    log.debug('start posting in {} group'.format(group_id))

    # create api here coz celery through vk_api exception, idk why
    session = create_vk_session_using_login_password(login, password, app_id)
    api = session.get_api()

    try:
        group = Group.objects.get(group_id=group_id)
        record = Record.objects.get(pk=record_id)
    except:
        log.error('got unexpected exception in post_record for group {}'.format(group_id), exc_info=True)
        return

    if not session:
        log.error('session not created in group {}'.format(group_id))
        record.is_involved_now = False
        record.save(update_fields=['is_involved_now'])
        return

    if not api:
        log.error('no api was created in group {}'.format(group_id))
        record.is_involved_now = False
        record.save(update_fields=['is_involved_now'])
        return

    try:
        attachments = []

        record_text = record.text

        if group.is_replace_russian_with_english:
            record_text = replace_russian_with_english_letters(record_text)

        record_text = delete_hashtags_from_text(record_text)

        if group.is_text_delete_enabled:
            record_text = ''

        audios = list(record.audios.all())
        log.debug('got {} audios for group {}'.format(len(audios), group_id))

        if group.is_audios_shuffle_enabled and len(audios) > 1:
            shuffle(audios)
            log.debug('group {} {} audios shuffled'.format(group_id, len(audios)))

        for audio in audios:
            attachments.append('audio{}_{}'.format(audio.owner_id, audio.audio_id))

        # images part
        images = list(record.images.all())

        if group.is_merge_images_enabled:
            images = images[:6]

        log.debug('got {} images for group {}'.format(len(images), group_id))

        if group.is_photos_shuffle_enabled and len(images) > 1:
            shuffle(images)
            log.debug('group {} {} images shuffled'.format(group_id, len(images)))

        image_files = [download_file(image.url) for image in images[::-1]]

        if (
            group.is_merge_images_enabled
            and len(images) == 6
            and is_images_size_nearly_the_same(image_files, config.THE_SAME_SIZE_FACTOR)
            and is_all_images_vertical(image_files)
        ):
            old_image_files = image_files
            image_files = [merge_six_images_into_one(image_files)]
            delete_files(old_image_files)

        for image_local_filename in image_files:
            actions_to_unique_image = {}

            if group.is_image_mirror_enabled and not is_text_on_image(image_local_filename):
                actions_to_unique_image['mirror'] = True

            if group.RGB_image_tone:
                actions_to_unique_image['rgb_tone'] = group.RGB_image_tone

            max_text_to_fill_length = config.MAX_TEXT_TO_FILL_LENGTH
            if len(images) == 1 and group.is_text_filling_enabled and len(record_text) <= max_text_to_fill_length:
                actions_to_unique_image['text_to_fill'] = delete_emoji_from_text(record_text)
                record_text = ''

            percentage_to_crop_from_edges = config.PERCENTAGE_TO_CROP_FROM_EDGES
            if (
                not group.is_merge_images_enabled
                and group.is_changing_image_to_square_enabled
                and not is_text_on_image(image_local_filename)
            ):
                actions_to_unique_image['crop_to_square'] = percentage_to_crop_from_edges

            prepare_image_for_posting(image_local_filename, **actions_to_unique_image)

            attachments.append(upload_photo(session, image_local_filename, group_id))

        delete_files(image_files)

        # gif part
        gifs = record.gifs.all()
        log.debug('got {} gifs for group {}'.format(len(gifs), group_id))
        if gifs and check_docs_availability(api, ['{}_{}'.format(gif.owner_id, gif.gif_id) for gif in gifs]):
            for gif in gifs:
                attachments.append('doc{}_{}'.format(gif.owner_id, gif.gif_id))
        elif gifs:
            record.failed_date = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            record.is_involved_now = False
            record.save(update_fields=['failed_date', 'is_involved_now'])
            return

        videos = record.videos.all()
        log.debug('got {} videos in attachments for group {}'.format(len(videos), group_id))
        for video in videos:
            if check_video_availability(api, video.owner_id, video.video_id):
                attachments.append('video{}_{}'.format(video.owner_id, video.video_id))
            else:
                record.failed_date = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                record.is_involved_now = False
                record.save(update_fields=['failed_date', 'is_involved_now'])
                return

        additional_texts = group.additional_texts.all().order_by('id')
        if additional_texts:
            additional_text = next((text for text in additional_texts if text.id > group.last_used_additional_text_id),
                                   additional_texts[0])
            log.debug(f'Found additional texts for group {group.domain_or_id}. '
                      f'Last used text id: {group.last_used_additional_text_id}, '
                      f'new text id: {additional_text.id}, new text: {additional_text.text}')

            group.last_used_additional_text_id = additional_text.id
            group.save(update_fields=['last_used_additional_text_id'])

            if record_text:
                record_text = '\n'.join([record_text, additional_text.text])
            else:
                record_text = additional_text.text

        post_response = api.wall.post(owner_id='-{}'.format(group_id),
                                      from_group=1,
                                      message=record_text,
                                      attachments=','.join(attachments))
        log.debug('{} in group {}'.format(post_response, group_id))
    except vk_api.VkApiError as error_msg:
        log.info('group {} got api error: {}'.format(group_id, error_msg))
        record.failed_date = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        record.is_involved_now = False
        record.save(update_fields=['failed_date', 'is_involved_now'])
        return
    except:
        log.error('caught unexpected exception in group {}'.format(group_id), exc_info=True)
        record.failed_date = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        record.is_involved_now = False
        record.save(update_fields=['failed_date', 'is_involved_now'])
        return

    record.post_in_group_id = post_response.get('post_id', 0)
    record.post_in_group_date = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    record.group = group
    record.is_involved_now = False
    record.save()
    log.debug('post in group {} finished'.format(group_id))


@task
def pin_best_post():
    """

    :return:
    """

    active_groups = Group.objects.filter(
        user__isnull=False,
        is_posting_active=True,
        is_pin_enabled=True).distinct()

    tokens = [token.app_service_token for token in ServiceToken.objects.all()]
    log.info('working with {} tokens: {}'.format(len(tokens), tokens))

    if not tokens:
        log.error('Got no tokens!')
        return

    for group in active_groups:
        token = choice(tokens)
        log.debug('work with token {}'.format(token))
        search_api = create_vk_api_using_service_token(token)
        time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=24)
        log.debug('search for posts from {} to now'.format(time_threshold))

        records_count = config.WALL_RECORD_COUNT_TO_PIN
        wall = [record for record in get_wall(search_api, group.domain_or_id, count=records_count)['items']
                if datetime.fromtimestamp(record['date'], tz=timezone.utc) >= time_threshold]

        if wall:
            log.debug('got {} wall records in last 24 hours'.format(len(wall)))

            try:
                best = max(wall, key=lambda item: item['likes']['count'])
            except KeyError:
                log.error('failed to fetch best record', exc_info=True)
                continue
            log.debug('got best record with id: {}'.format(best['id']))

            session = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id)
            api = session.get_api()

            group.group_id = fetch_group_id(api, group.domain_or_id)
            group.save(update_fields=['group_id'])

            try:
                response = api.wall.pin(owner_id='-{}'.format(group.group_id),
                                        post_id=best['id'])
                log.debug(response)
            except:
                log.error('failed to pin post', exc_info=True)
                continue

        else:
            log.warning('have no post in last 24 hours')
            continue


@task
def delete_old_ads():
    """

    :return:
    """
    log.info('delete_old_ads called')

    active_groups = Group.objects.filter(
        user__isnull=False,
        is_posting_active=True,
        is_pin_enabled=True).distinct()

    for group in active_groups:

        hours = config.OLD_AD_RECORDS_HOURS
        time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=hours)

        ads = AdRecord.objects.filter(group=group, post_in_group_date__lt=time_threshold)
        log.debug('got {} ads in last 30 hours in group {}'.format(len(ads), group.group_id))

        if len(ads):

            session = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id)
            if not session:
                continue

            api = session.get_api()
            if not api:
                continue

            ignore_ad_ids = []

            for ad in ads:
                try:
                    resp = api.wall.delete(owner_id='-{}'.format(group.group_id),
                                           post_id=ad.ad_record_id)
                    log.debug('delete_old_ads {} response: {}'.format(ad.ad_record_id, resp))
                except:
                    log.error('got unexpected error in delete_old_ads for {}'.format(ad.ad_record_id), exc_info=True)
                    ignore_ad_ids.append(ad.id)
                    continue

            ads = ads.exclude(pk__in=ignore_ad_ids)
            number_of_records, extended = ads.delete()
            log.debug('delete {} ads out of db'.format(number_of_records))
        log.info('finish deleting old ads')


@task
def update_statistics():
    log.debug('update_statistics called')

    now_time = datetime.now(tz=timezone.utc)
    today_start = now_time.replace(hour=0, minute=0, second=0)
    yesterday_start = today_start - timedelta(hours=24)

    all_groups = Group.objects.all()
    all_group_ids = all_groups.values_list('domain_or_id', flat=True)
    log.debug('got {} groups in update_statistics'.format(len(all_group_ids)))

    token = ServiceToken.objects.filter().first().app_service_token
    log.debug('using {} token for update_statistics'.format(token))

    api = create_vk_api_using_service_token(token)

    if not api:
        log.error('cannot update statistics')

    try:
        response = api.groups.getById(group_ids=all_group_ids, fields=['members_count'])

        for piece in response:

            screen_name = piece.get('screen_name', None)
            members_count_now = piece.get('members_count', None)
            group_id = piece.get('id', None)

            try:
                group = all_groups.get(domain_or_id=group_id)
            except ObjectDoesNotExist:
                group = all_groups.get(domain_or_id=screen_name)

            if group:
                members_count_last = group.members_count or 0
                group.members_growth = members_count_now - members_count_last
                group.members_count = members_count_now

                starts = Q(post_in_group_date__gte=yesterday_start)
                ends = Q(post_in_group_date__lte=today_start)

                group.number_of_posts_yesterday = \
                    Record.objects.filter(group_id=group.domain_or_id).filter(starts & ends).count() + \
                    Horoscope.objects.filter(group_id=group.domain_or_id).filter(starts & ends).count()

                group.number_of_ad_posts_yesterday = AdRecord.objects.filter(group_id=group.domain_or_id).\
                    filter(starts & ends).count()

                group.statistics_last_update_date = now_time.strftime('%Y-%m-%d %H:%M:%S')

                group.save(update_fields=['members_growth',
                                          'members_count',
                                          'number_of_posts_yesterday',
                                          'number_of_ad_posts_yesterday',
                                          'statistics_last_update_date'])

                log.debug('finish updating statistic for group {} {}'.format(group_id, screen_name))
            else:
                log.warning('problem with group {} {}'.format(group_id, screen_name))

    except:
        log.debug('got unexpected error in update_statistics', exc_info=True)
        return

    log.debug('update_statistics finished successfully')


@task
def sex_statistics_weekly():
    log.debug('sex_statistics_weekly started')

    now_time = datetime.now(tz=timezone.utc)

    all_groups = Group.objects.all()
    log.debug('got {} groups in sex_statistics_weekly'.format(len(all_groups)))

    for group in all_groups:
        session = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id)
        if not session:
            continue

        api = session.get_api()
        if not api:
            continue

        stats = get_group_week_statistics(api, group_id=group.group_id)

        male_count_list = []
        female_count_list = []

        for day in stats:
            sex_list = day.get('sex')
            for sex in sex_list:
                if sex.get('value') == 'f':
                    female_count_list.append(sex.get('visitors'))
                elif sex.get('value') == 'm':
                    male_count_list.append(sex.get('visitors'))

        male_average_count = sum(male_count_list)//len(male_count_list)
        female_average_count = sum(female_count_list)//len(female_count_list)

        group.male_weekly_average_count = male_average_count
        group.female_weekly_average_count = female_average_count
        group.sex_last_update_date = now_time.strftime('%Y-%m-%d %H:%M:%S')

        group.save(update_fields=['male_weekly_average_count', 'female_weekly_average_count', 'sex_last_update_date'])

    log.debug('sex_statistics_weekly finished')
