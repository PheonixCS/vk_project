# celery instance file
from __future__ import absolute_import, unicode_literals

import os

import celery.signals
from celery import Celery

# TODO figure out why 
os.environ['DJANGO_SETTINGS_MODULE'] = 'vk_scraping_posting.settings'
# os.environ.setdefault('DJANGO_SETTING_MODULE', 'vk_scraping_posting.settings')

app = Celery('vk_scraping_posting')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.task(bind=True)


@celery.signals.setup_logging.connect
def on_celery_setup_logging(**kwargs):
    pass


def debug_task(self):
    print('request: {0!r}'.format(self.request))
