import os
from celery import Celery

# app = Celery('tasks', backend='redis://localhost:6379',
#              broker='redis://localhost:6379', include=['polygon.tasks'])
app = Celery('tasks', backend=os.environ['CELERY_BACKEND'],
             broker=os.environ['CELERY_BROKER'], include=['polygon.tasks'])

# app.autodiscover_tasks(['polygon'])


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
