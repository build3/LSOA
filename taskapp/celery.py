import os

from celery import Celery
from django.apps import AppConfig
from django.conf import settings

if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

app = Celery(settings.APP_NAME)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


class CeleryConfig(AppConfig):
    name = 'taskapp'
    verbose_name = 'Celery Config'


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
