import re
import logging

from alphabet_detector import AlphabetDetector
from urlextract import URLExtract
from vk_api import ApiError

from settings.models import Setting

log = logging.getLogger('moderation.checks')

VK_API_VERSION = Setting.get_value(key='VK_API_VERSION')


def is_post_ad(api, post_id, group_id):
    try:
        post = api.wall.getById(posts='-{}_{}'.format(group_id, post_id),
                                api_version=VK_API_VERSION)
    except ApiError as error_msg:
        log.error('Group {} post {} got api error in getById method: {}'.format(group_id, post_id, error_msg))
        return None
    return post[0].get('marked_as_ads', False)


def is_stop_words_in_text(stop_list, text):
    if any(word in stop_list for word in text):
        log.debug('found stop word in text')
        return True


def is_scam_words_in_text(text):
    for word in text:
        ad = AlphabetDetector()
        if len(ad.detect_alphabet(word)) > 1:
            log.debug('found scam word in text')
            return True


def is_video_in_attachments(attachments):
    for attachment in attachments:
        if attachment['type'] == 'video':
            log.debug('found video in attachments')
            return True


def is_link_in_attachments(attachments):
    for attachment in attachments:
        if attachment['type'] == 'link':
            log.debug('found link in attachments')
            return True


def is_group(commentator_id):
    if int(commentator_id) < 0:
        log.debug('from_id if group')
        return True


# TODO fix emojilink: ;vk.com
def is_links_in_text(text):
    extractor = URLExtract()
    if extractor.has_urls(text):
        log.debug('found url in text')
        return True


def is_vk_links_in_text(text):
    if re.findall(r'\[.*?\|.*?\]', text):
        log.debug('found vk link in text')
        return True


def is_audio_and_photo_in_attachments(attachments):
    if [attachment for attachment in attachments if attachment['type'] == 'photo'] and \
            [attachment for attachment in attachments if attachment['type'] == 'audio']:
        log.debug('found audio + photo in attachments')
        return True

