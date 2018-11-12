import os

import vk_api

from posting.poster import download_file
import logging


log = logging.getLogger('services.vk.files')


def upload_video(session, video_local_filename, group_id, name, description):
    log.debug('upload_video called')

    try:
        upload = vk_api.VkUpload(session)
        video = upload.video(video_file=video_local_filename,
                             group_id=int(group_id),
                             name=name,
                             description=description,
                             no_comments=True)
    except:
        log.error('exception while uploading video', exc_info=True)
        return

    return 'video{}_{}'.format(video['owner_id'], video['video_id'])


def upload_gif(session, gif_url):
    log.debug('upload_gif called')
    gif_local_filename = download_file(gif_url, 'gif')

    try:
        upload = vk_api.VkUpload(session)
        gif = upload.document(doc=gif_local_filename)
    except:
        log.error('exception while uploading gif', exc_info=True)
        return

    if os.path.isfile(gif_local_filename):
        os.remove(gif_local_filename)

    return 'doc{}_{}'.format(gif[0]['owner_id'], gif[0]['id'])


def upload_photo(session, image_local_filepath, group_id):
    log.debug('upload_photo called')

    try:
        upload = vk_api.VkUpload(session)
        photo = upload.photo_wall(photos=image_local_filepath,
                                  group_id=int(group_id))
    except:
        log.error('exception while uploading photo', exc_info=True)
        return

    return 'photo{}_{}'.format(photo[0]['owner_id'], photo[0]['id'])


def check_docs_availability(api, docs):
    """

    :param docs: list of dictionaries
    :type docs: list
    :return: true if all docs are available
    :rtype: bool
    """
    log.debug('check_docs_availability called')

    try:
        resp = api.docs.getById(docs=','.join(docs))

        if len(resp) == len(docs):
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
        resp = api.video.get(owner_id=owner_id, videos='{}_{}'.format(owner_id, video_id))

        if resp.get('items'):
            return True
        else:
            log.info('check_video_availability failed')
            return False

    except:
        log.error('got unexpected error in check_video_availability', exc_info=True)