from time import time

import celery
import celery.states
from celery.events import Event
from celery.utils import uuid
from prometheus_client import REGISTRY
from unittest import TestCase
from unittest.mock import patch

from celery_prometheus_exporter import (
    WorkerMonitoringThread, setup_metrics, MonitorThread
)

from celery_test_utils import get_celery_app


class TestMockedCelery(TestCase):

    def setUp(self):
        setup_metrics()  # reset metrics

    def test_initial_metric_values(self):
        for state in celery.states.ALL_STATES:
            assert REGISTRY.get_sample_value(
                'celery_tasks', labels=dict(state=state)) == 0
        assert REGISTRY.get_sample_value('celery_workers') == 0
        assert REGISTRY.get_sample_value('celery_task_latency_count') == 0
        assert REGISTRY.get_sample_value('celery_task_latency_sum') == 0

    def test_workers_count(self):
        app = get_celery_app()
        assert REGISTRY.get_sample_value('celery_workers') == 0

        with patch.object(app.control, 'ping') as mock_ping:
            w = WorkerMonitoringThread(app=app)

            mock_ping.return_value = []
            w.update_workers_count()
            assert REGISTRY.get_sample_value('celery_workers') == 0

            mock_ping.return_value = [0]  # 1 worker
            w.update_workers_count()
            assert REGISTRY.get_sample_value('celery_workers') == 1

            mock_ping.return_value = [0, 0]  # 2 workers
            w.update_workers_count()
            assert REGISTRY.get_sample_value('celery_workers') == 2

            mock_ping.return_value = []
            w.update_workers_count()
            assert REGISTRY.get_sample_value('celery_workers') == 0

    def test_tasks_events(self):
        app = get_celery_app()
        task_uuid = uuid()
        task_name = 'mytask'
        hostname = 'myhost'
        local_received = time()
        latency_before_started = 123.45
        runtime = 234.5

        m = MonitorThread(app=app)

        for state in celery.states.ALL_STATES:
            assert REGISTRY.get_sample_value(
                'celery_tasks', labels=dict(state=state)) == 0
        assert REGISTRY.get_sample_value('celery_task_latency_count') == 0
        assert REGISTRY.get_sample_value('celery_task_latency_sum') == 0

        m._process_task_received(Event(
            'task-received', uuid=task_uuid, name=task_name,
            args='()', kwargs='{}', retries=0, eta=None, hostname=hostname,
            clock=0,
            local_received=local_received))

        for state in celery.states.ALL_STATES - {celery.states.RECEIVED}:
            assert REGISTRY.get_sample_value(
                'celery_tasks', labels=dict(state=state)) == 0

        for state in {celery.states.RECEIVED}:
            assert REGISTRY.get_sample_value(
                'celery_tasks', labels=dict(state=state)) == 1

        m._process_task_started(Event(
            'task-started', uuid=task_uuid, hostname=hostname,
            clock=1,
            local_received=local_received + latency_before_started))

        for state in celery.states.ALL_STATES - {celery.states.STARTED}:
            assert REGISTRY.get_sample_value(
                'celery_tasks', labels=dict(state=state)) == 0

        for state in {celery.states.STARTED}:
            assert REGISTRY.get_sample_value(
                'celery_tasks', labels=dict(state=state)) == 1

        m._process_event(Event(
            'task-succeeded', uuid=task_uuid, result='42',
            runtime=runtime, hostname=hostname, clock=2,
            local_received=local_received + latency_before_started + runtime))

        for state in celery.states.ALL_STATES - {celery.states.SUCCESS}:
            assert REGISTRY.get_sample_value(
                'celery_tasks', labels=dict(state=state)) == 0

        for state in {celery.states.SUCCESS}:
            assert REGISTRY.get_sample_value(
                'celery_tasks', labels=dict(state=state)) == 1

        assert REGISTRY.get_sample_value('celery_task_latency_count') == 1
        self.assertAlmostEqual(REGISTRY.get_sample_value(
            'celery_task_latency_sum'), latency_before_started)
