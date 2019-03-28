import celery
import time
from kombu import Queue, Exchange


def get_celery_app(queue=None):
    app = celery.Celery(broker='memory://', backend='cache+memory://')

    if queue:
        app.conf.update(
            CELERY_DEFAULT_QUEUE=queue,
            CELERY_QUEUES=(
                Queue(queue, exchange=Exchange(queue, type='direct'), routing_key=queue),
            ),
            CELERY_ROUTES={
                'task1': {'queue': queue, 'routing_key': queue},
            }
        )

    return app


class SampleTask(celery.Task):
    name = 'sample-task'

    def run(self, *args, **kwargs):
        time.sleep(10)
