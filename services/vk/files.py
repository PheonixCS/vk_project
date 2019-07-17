import logging

import vk_api

from posting.core.poster import download_file
from tenacity import retry, stop_after_attempt, wait_fixed, before_sleep_log

log = logging.getLogger('services.vk.files')


def upload_video(session, video_local_path, group_id, name, description):
    log.debug('upload_video called')

    try:
        upload = vk_api.VkUpload(session)
        video = upload.video(
            video_file=video_local_path,
            group_id=int(group_id),
            name=name,
            description=description,
            no_comments=True
        )
    except vk_api.VkApiError:
        log.error('vk exception while uploading video', exc_info=True)
        return

    owner_id, video_id = video.get('owner_id'), video.get('video_id')

    if owner_id and video_id:
        return 'video{}_{}'.format(owner_id, video_id)


def upload_gif(session, gif_url):
    log.debug('upload_gif called')

    gif_local_filename = download_file(gif_url, 'gif')

    try:
        upload = vk_api.VkUpload(session)
        gif = upload.document(doc=gif_local_filename)
    except vk_api.VkApiError:
        log.error('vk exception while uploading gif', exc_info=True)
        return

    if gif and isinstance(gif, list):
        owner_id, gif_id = gif[0].get('owner_id'), gif[0].get('id')

        if owner_id and gif_id:
            return 'doc{}_{}'.format(owner_id, gif_id)


@retry(reraise=True, stop=stop_after_attempt(2), wait=wait_fixed(0.3),
       before_sleep=before_sleep_log(log, logging.DEBUG))
def upload_photos(session: vk_api.VkApi, image_local_path: list or str, group_id: str) -> list or str or None:
    log.debug('upload_photo called')

    if not (isinstance(image_local_path, str) or isinstance(image_local_path, list)):
        raise TypeError('upload_photo support only one or several photos as list')

    # try:
    #     upload = vk_api.VkUpload(session)
    #     upload_result = upload.photo_wall(
    #         photos=image_local_path,
    #         group_id=int(group_id)
    #     )
    # except vk_api.VkApiError:
    #     log.error('vk exception while uploading photo', exc_info=True)
    #     return
    upload = vk_api.VkUpload(session)
    upload_result = upload.photo_wall(
        photos=image_local_path,
        group_id=int(group_id)
    )

    if upload_result and isinstance(upload_result, list):
        result = ['photo{}_{}'.format(item.get('owner_id'), item.get('id')) for item in upload_result]

        if isinstance(image_local_path, str):
            return result[0]
        else:
            return result


def check_docs_availability(api, docs):
    """

    :param api: api object
    :param docs: list of dictionaries
    :type docs: list
    :return: true if all docs are available
    :rtype: bool
    """
    log.debug('check_docs_availability called')

    try:
        resp = api.docs.getById(docs=','.join(docs))

        if isinstance(resp, list) and len(resp) == len(docs):
            return True
        else:
            log.info('check_docs_availability failed')
            return False
    except:
        log.error('got unexpected error in check_docs_availability', exc_info=True)


def check_video_availability(api, owner_id, video_id):
    """

    :param api: api object
    :param video_id: video id from vk
    :param owner_id: string  representing video owner in vk way
    :return: true if video available
    """
    log.debug('check_video_availability called')

    try:
        resp = api.video.get(owner_id=owner_id, videos=f'{owner_id}_{video_id}')

        if resp.get('items'):
            return True
        else:
            log.info('check_video_availability failed')
            return False
    except:
        log.error('got unexpected error in check_video_availability', exc_info=True)
