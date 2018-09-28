"""
Django settings for vk_scraping_posting project.

Generated by 'django-admin startproject' using Django 2.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import sentry_sdk
import logging
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from celery.schedules import crontab

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CELERYD_HIJACK_ROOT_LOGGER = False
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'amqp://localhost:5672')
CELERY_BEAT_SCHEDULE = {
    'scraper_task': {
        'task': 'scraping.tasks.run_scraper',
        'schedule': crontab(minute=0)  # every hour at 0 minute
    },
    'poster_task': {
        'task': 'posting.tasks.examine_groups',
        'schedule': crontab(minute='*')  # every minute
    },
    'pin_best_task': {
        'task': 'posting.tasks.pin_best_post',
        'schedule': crontab(minute=1, hour='1')  # at 1:01 am UTC (4:01 am by MSK)
    },
    'delete_old_task': {
        'task': 'scraping.tasks.delete_oldest',
        'schedule': crontab(minute=15, hour=5)  # at 5:15 am UTC (8:15 am by MSK)
    },
    'delete_old_ads': {
        'task': 'posting.tasks.delete_old_ads',
        'schedule': crontab(minute=30)  # every hour at 30 minute
    },
    'delete_old_horoscope_records': {
        'task': 'scraping.tasks.delete_old_horoscope_records',
        'schedule': crontab(minute=0, hour=0)  # at 0:00 am UTC (3:00 am by MSK)
    },
    'delete_old_transactions': {
        'task': 'moderation.tasks.delete_old_transactions',
        'schedule': crontab(minute=0, hour=0)  # at 0:00 am UTC (3:00 am by MSK)
    },
    'update_statistics': {
        'task': 'posting.tasks.update_statistics',
        'schedule': crontab(minute=5, hour=1)  # at 0:05 am UTC (3:05 am by MSK)
    },
    'process_moderation_transaction': {
        'task': 'moderation.tasks.process_transactions',
        'schedule': crontab(minute='*')  # every minute
    },
    'ban_donors_admins': {
        'task': 'moderation.tasks.ban_donors_admins',
        'schedule': crontab(minute=0, hour=0)  # at 0:00 am UTC (3:00 am by MSK)
    },
    'sex_statistics_weekly': {
        'task': 'posting.tasks.sex_statistics_weekly',
        'schedule': crontab(minute=0, hour=0, day_of_week=0)  # at 0:00 am UTC every sunday (3:00 am by MSK)
    }
}


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '3(p-@#k$mrd0_*lw=u%kh7%oh!vp9iv@anxxk)-bcbbvup4^^0'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['46.101.217.6', '127.0.0.1', '80.211.178.81']

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'scraping',
    'posting',
    'moderation',

    'constance.backends.database',
    'constance',

    'raven.contrib.django.raven_compat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vk_scraping_posting.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'vk_scraping_posting.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'vk_db'),
        'USER': os.environ['DB_LOGIN'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ['DB_PORT'],
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

sentry_logging = LoggingIntegration(
    level=logging.INFO,  # Capture info and above as breadcrumbs
    event_level=None     # Send no events from log messages
)

sentry_sdk.init(
    dsn="https://374beeda2c78426ea8cd2cc84d176b1b@sentry.io/1290864",
    integrations=[DjangoIntegration(), CeleryIntegration(), sentry_logging]
)


from .default_config import *

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
            'when': 'D',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'default'
        },
        'django': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/django.log",
            'when': 'D',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'default'
        },
        'moderation': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/moderation.log",
            'when': 'D',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'default'
        },
        'scraping': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/scraping.log",
            'when': 'D',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'default'
        },
        'posting': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/posting.log",
            'when': 'D',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'default'
        },
        '': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/test.log",
            'when': 'D',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'default'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'django'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG')
        },
        'scraping': {
            'handlers': ['scraping'],
            'level': os.getenv('SCRAPER_LOG_LEVEL', 'DEBUG')
        },
        'posting': {
            'handlers': ['posting'],
            'level': os.getenv('POSTING_LOG_LEVEL', 'DEBUG')
        },
        'moderation': {
            'handlers': ['moderation'],
            'level': os.getenv('MODERATION_LOG_LEVEL', 'DEBUG')
        },
        'сelery': {
            'handlers': ['console', 'celery'],
            'level': os.getenv('CELERY_LOG_LEVEL', 'DEBUG')
        },
    },
}
