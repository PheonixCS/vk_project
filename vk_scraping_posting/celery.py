# celery instance file
from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

# TODO figure out why 
os.environ['DJANGO_SETTINGS_MODULE'] = 'vk_scraping_posting.settings'
# os.environ.setdefault('DJANGO_SETTING_MODULE', 'vk_scraping_posting.settings')

app = Celery('vk_scraping_posting')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.task(bind=True)


def debug_task(self):
    print('request: {0!r}'.format(self.request))
