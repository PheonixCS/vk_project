"""
Django settings for vk_scraping_posting project.

Generated by 'django-admin startproject' using Django 2.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
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
        'schedule': 60  # every 60 seconds
    },
    'pin_best_task': {
        'task': 'posting.tasks.pin_best_post',
        'schedule': crontab(minute=0, hour='6')  # at 6 am
    },
    'delete_old_task': {
        'task': 'scraping.tasks.delete_oldest',
        'schedule': crontab(minute=0, hour=0)  # at midnight
    }
}


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '3(p-@#k$mrd0_*lw=u%kh7%oh!vp9iv@anxxk)-bcbbvup4^^0'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['46.101.217.6', '127.0.0.1']


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
    'settings',
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
        'NAME': 'vk_scr_pos_db',
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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

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
        'apps': {
            'level': 'DEBUG',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/test.log",
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
        },
        'celery': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/celery.log",
            'formatter': 'default',
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
        },
        'django': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.getenv('LOGGING_DIR', BASE_DIR) + "/django.log",
            'formatter': 'default',
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'django'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG')
        },
        'scraping': {
            'handlers': ['apps'],
            'level': os.getenv('SCRAPER_LOG_LEVEL', 'DEBUG')
        },
        'posting': {
            'handlers': ['apps'],
            'level': os.getenv('POSTING_LOG_LEVEL', 'DEBUG')
        },
        'moderation': {
            'handlers': ['apps'],
            'level': os.getenv('MODERATION_LOG_LEVEL', 'DEBUG')
        },
        'сelery': {
            'handlers': ['console', 'celery'],
            'level': os.getenv('CELERY_LOG_LEVEL', 'DEBUG')
        },
    },
}