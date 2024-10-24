import logging
import os

import requests

from vk_scraping_posting.settings import BASE_DIR

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')


class TelegramHandler(logging.Handler):
    def emit(self, record):
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            print('lol <{}> <{}>'.format(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))
            return

        log_entry = self.format(record)
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': log_entry,
            'parse_mode': 'HTML'
        }
        return requests.post('https://api.telegram.org/bot{token}/sendMessage'.format(token=TELEGRAM_TOKEN),
                             data=payload).content


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(funcName)20s: %(message)s',
        }
    },

    'filters': {
        'rate_limit': {
            '()': 'ratelimitingfilter.RateLimitingFilter',
            'rate': 5,
            'per': 60*10,  # 10 minutes
            'burst': 5
        }
    },

    'handlers': {
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        },
        'celery': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/celery.log",
            'formatter': 'default'
        },
        'django': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/django.log",
            'formatter': 'default'
        },
        'moderation': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/moderation.log",
            'formatter': 'default'

        },
        'scraping': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/scraping.log",
            'formatter': 'default'
        },
        'posting': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/posting.log",
            'formatter': 'default'
        },
        'services': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/services.log",
            'formatter': 'default'
        },
        'telegram': {
            'level': 'DEBUG',
            'class': 'vk_scraping_posting.log_settings.TelegramHandler',
        },
        '': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/other.log",
            'formatter': 'default'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'django'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': False
        },
        'scraping': {
            'handlers': ['scraping'],
            'level': os.getenv('SCRAPER_LOG_LEVEL', 'DEBUG'),
            'propagate': False
        },
        'posting': {
            'handlers': ['posting'],
            'level': os.getenv('POSTING_LOG_LEVEL', 'DEBUG'),
            'propagate': False
        },
        'moderation': {
            'handlers': ['moderation'],
            'level': os.getenv('MODERATION_LOG_LEVEL', 'DEBUG'),
            'propagate': False
        },
        'сelery': {
            'handlers': ['console', 'celery'],
            'level': os.getenv('CELERY_LOG_LEVEL', 'DEBUG'),
            'propagate': False
        },
        'services': {
            'handlers': ['services'],
            'level': os.getenv('CELERY_LOG_LEVEL', 'DEBUG'),
            'propagate': True
        },
        '': {
            'handlers': [''],
            'level': os.getenv('CELERY_LOG_LEVEL', 'DEBUG'),
            'propagate': True
        }
    },
}
