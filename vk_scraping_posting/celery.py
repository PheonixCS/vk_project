# celery instance file
from __future__ import absolute_import

import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTING_MODULE', 'vk_scraping_posting.settings')

app = Celery('vk_scraping_posting')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.task(bind=True)


def debug_task(self):
    print('request: {0!r}'.format(self.request))
