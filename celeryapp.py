from celery import Celery
from kombu import Queue, Exchange

import os
import time

BROKER_URL = os.getenv("BROKER_URL")
RESULT_BACKEND_URL = os.getenv("RESULT_BACKEND_URL", None)

celery_app = Celery(
    broker=BROKER_URL,
)

if RESULT_BACKEND_URL:
    celery_app.conf.update(backend=RESULT_BACKEND_URL)

celery_app.conf.update(
    CELERY_DEFAULT_QUEUE="queue1",
    CELERY_QUEUES=(
        Queue('queue1', exchange=Exchange('queue1', type='direct'), routing_key='queue1'),
        Queue('queue2', exchange=Exchange('queue2', type='direct'), routing_key='queue2'),
        Queue('queue3', exchange=Exchange('queue3', type='direct'), routing_key='queue3'),
    ),
    CELERY_ROUTES={
        'task1': {'queue': 'queue1', 'routing_key': 'queue1'},
        'task2': {'queue': 'queue2', 'routing_key': 'queue2'},
        'task3': {'queue': 'queue3', 'routing_key': 'queue3'},
    }
)

@celery_app.task
def task1():
    time.sleep(20)

@celery_app.task
def task2():
    time.sleep(20)

@celery_app.task
def task3():
    time.sleep(20)
