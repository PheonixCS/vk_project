import logging
import os

import requests
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration, ignore_logger

from vk_scraping_posting.settings import BASE_DIR

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

ignore_logger('telegram')


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


sentry_logging = LoggingIntegration(
    level=logging.INFO,  # Capture info and above as breadcrumbs
    event_level=logging.WARNING  # Send no events from log messages
)

if os.getenv('SERVER_ROLE', 'prod') == 'prod':
    sentry_sdk.init(
        dsn="https://374beeda2c78426ea8cd2cc84d176b1b@sentry.io/1290864",
        integrations=[DjangoIntegration(), CeleryIntegration(), sentry_logging]
    )

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
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
            'propagate': True
        },
        'scraping': {
            'handlers': ['scraping'],
            'level': os.getenv('SCRAPER_LOG_LEVEL', 'DEBUG'),
            'propagate': True
        },
        'posting': {
            'handlers': ['posting'],
            'level': os.getenv('POSTING_LOG_LEVEL', 'DEBUG'),
            'propagate': True
        },
        'moderation': {
            'handlers': ['moderation'],
            'level': os.getenv('MODERATION_LOG_LEVEL', 'DEBUG'),
            'propagate': True
        },
        'сelery': {
            'handlers': ['console', 'celery'],
            'level': os.getenv('CELERY_LOG_LEVEL', 'DEBUG'),
            'propagate': True
        },
        'services': {
            'handlers': [''],
            'level': os.getenv('CELERY_LOG_LEVEL', 'DEBUG'),
            'propagate': True
        },
        'telegram': {
            'handlers': ['telegram'],
            'level': 'WARNING',
            'propagate': True,
            'filters': ['rate_limit']
        }
    },
}
