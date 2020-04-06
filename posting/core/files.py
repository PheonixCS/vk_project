import os
import logging

import requests

log = logging.getLogger('posting.files')


def download_file(url, extension=None):
    log.debug('download_file called')

    file_name_in_vk = url.split('/')[-1]
    extension = extension or file_name_in_vk.split('.')[-1]
    local_filename = str(abs(hash(url)))[:256]

    if extension:
        local_filename += '.{}'.format(extension)

    r = requests.get(url)
    with open(local_filename, 'wb') as f:
        f.write(r.content)

    log.debug('{} file downloaded'.format(local_filename))
    return local_filename


def delete_files(file_paths):
    log.debug('delete_files called with {} files'.format(len(file_paths)))

    if isinstance(file_paths, list):
        for file in file_paths:
            try:
                os.remove(file)
            except FileNotFoundError as exc:
                log.error('Fail to delete file {}'.format(exc))
                continue
    elif isinstance(file_paths, str):
        try:
            os.remove(file_paths)
        except FileNotFoundError as exc:
            log.error('Fail to delete file {}'.format(exc))
    else:
        log.warning('delete_files got wrong type')
        return
    log.debug('delete_files finished')
