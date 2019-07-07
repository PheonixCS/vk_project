import logging
import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


from vk_scraping_posting.settings import BASE_DIR

sentry_logging = LoggingIntegration(
    level=logging.INFO,  # Capture info and above as breadcrumbs
    event_level=logging.WARNING  # Send no events from log messages
)

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

    'handlers': {
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        },
        'celery': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/celery.log",
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'default'
        },
        'django': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/django.log",
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'default'
        },
        'moderation': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/moderation.log",
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'default'

        },
        'scraping': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/scraping.log",
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'default'
        },
        'posting': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/posting.log",
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'default'
        },
        '': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/other.log",
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
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
    },
}