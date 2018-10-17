import logging
import urllib.error as url_error

import pytube

log = logging.getLogger('services.youtube')


def download_trailer(url):
    log.debug('starting downloading trailer')
    # TODO make downloading try except smarter
    try:
        path = pytube.YouTube(url).streams.first().download()
    except url_error.URLError:
        # this exception may occur, see https://github.com/nficano/pytube/issues/278
        import ssl
        ssl._create_default_https_context = ssl._create_stdlib_context

        try:
            path = pytube.YouTube(url).streams.first().download()
        except:
            return ''

    # TODO check how catch VideoUnavailable
    # except pytube.__main__.VideoUnavailable:
    except:
        return ''

    log.debug('finished downloading trailer')
    return path
