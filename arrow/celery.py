from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arrow.settings')

backend = os.environ[
    'CELERY_BACKEND'] if 'CELERY_BACKEND' in os.environ.keys() else 'redis://localhost:6379'
broker = os.environ[
    'CELERY_BROKER'] if 'CELERY_BROKER' in os.environ.keys() else 'redis://localhost:6379'

app = Celery('arrow',
             broker=broker,
             backend=backend)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'update-contest-status-every-1-second': {
        'task': 'contests.tasks.update_contest_status',
        'schedule': 1.0,
    },
}


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

# debug_task.delay()
