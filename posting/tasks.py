#
import logging
from datetime import datetime, timedelta
from random import choice

import vk_api
from celery import task
from django.utils import timezone

from posting.models import Group, ServiceToken, AdRecord
from posting.poster import (create_vk_session_using_login_password, fetch_group_id, upload_photo,
                            delete_hashtags_from_text, get_ad_in_last_hour, check_docs_availability,
                            check_video_availability)
from scraping.models import Record
from scraping.scraper import get_wall, create_vk_api_using_service_token

log = logging.getLogger('posting.scheduled')


@task
def examine_groups():
    try:
        log.debug('start group examination')
        groups_to_post_in = Group.objects.filter(user__isnull=False,
                                                 donors__isnull=False,
                                                 is_posting_active=True).distinct()

        log.debug('got {} groups'.format(len(groups_to_post_in)))

        now_minute = datetime.now().minute

        time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=1, minutes=5)
        allowed_time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=8)

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

            try:
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
                        post_horoscope.delay(group.user.login,
                                             group.user.password,
                                             group.user.app_id,
                                             group.group_id,
                                             group.horoscopes.filter(post_in_group_date__isnull=True).last().id)
                    except:
                        log.error('got unexpected exception in examine_groups', exc_info=True)
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
                                                post_in_group_date__isnull=True,
                                                failed_date__isnull=True,
                                                post_in_donor_date__gt=allowed_time_threshold)]
                log.debug('got {} ready to post records to group {}'.format(len(records), group.group_id))
                if not records:
                    continue

                record_with_max_rate = max(records, key=lambda x: x.rate)
                log.debug('record {} got max rate for group {}'.format(record_with_max_rate, group.group_id))

                try:
                    post_record.delay(group.user.login,
                                      group.user.password,
                                      group.user.app_id,
                                      group.group_id,
                                      record_with_max_rate.id)
                except:
                    log.error('got unexpected exception in examine_groups', exc_info=True)
    except:
        log.error('got unexpected exception in examine_groups', exc_info=True)

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
        attachments = ''
        if horoscope_record.image_url:
            attachments = upload_photo(session, horoscope_record.image_url, group_id)

        post_response = api.wall.post(owner_id='-{}'.format(group_id),
                                      from_group=1,
                                      message=delete_hashtags_from_text(horoscope_record.text),
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
        return

    if not api:
        log.error('no api was created in group {}'.format(group_id))
        return

    try:
        attachments = list()

        audios = record.audios.all()
        log.debug('got {} audios for group {}'.format(len(audios), group_id))
        for audio in audios:
            attachments.append('audio{}_{}'.format(audio.owner_id, audio.audio_id))

        images = record.images.all()
        log.debug('got {} images for group {}'.format(len(images), group_id))
        for image in images[::-1]:
            attachments.append(upload_photo(session, image.url, group_id))

        gifs = record.gifs.all()
        log.debug('got {} gifs for group {}'.format(len(gifs), group_id))
        if gifs and check_docs_availability(api, ['{}_{}'.format(gif.owner_id, gif.gif_id) for gif in gifs]):
            for gif in gifs:
                attachments.append('doc{}_{}'.format(gif.owner_id, gif.gif_id))
        elif gifs:
            record.failed_date = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            record.save()
            return

        videos = record.videos.all()
        log.debug('got {} videos in attachments for group {}'.format(len(videos), group_id))
        for video in videos:
            if check_video_availability(api, video.owner_id, video.video_id):
                attachments.append('video{}_{}'.format(video.owner_id, video.video_id))
            else:
                record.failed_date = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                record.save()
                return

        post_response = api.wall.post(owner_id='-{}'.format(group_id),
                                      from_group=1,
                                      message=delete_hashtags_from_text(record.text),
                                      attachments=','.join(attachments))
        log.debug('{} in group {}'.format(post_response, group_id))
    except vk_api.VkApiError as error_msg:
        log.info('group {} got api error: {}'.format(group_id, error_msg))
        return
    except:
        log.error('caught unexpected exception in group {}'.format(group_id), exc_info=True)
        return

    record.post_in_group_date = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    record.group = group
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

        # TODO count in live settings
        wall = [record for record in get_wall(search_api, group.domain_or_id, count=50)['items']
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

        # TODO hours in live settings
        time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=30)

        ads = AdRecord.objects.filter(group=group, post_in_group_date__lt=time_threshold)
        log.debug('got {} ads in last 30 hours in group {}'.format(len(ads), group.group_id))

        if len(ads):

            session = create_vk_session_using_login_password(group.user.login, group.user.password, group.user.app_id)
            if not session:
                continue

            api = session.get_api()
            if not api:
                continue

            for ad in ads:
                try:
                    resp = api.wall.delete(owner_id='-{}'.format(group.group_id),
                                           post_id=ad.ad_record_id)
                    log.debug('delete_old_ads {} response: {}'.format(ad.ad_record_id, resp))
                except:
                    log.error('got unexpected error in delete_old_ads for {}'.format(ad.ad_record_id), exc_info=True)
