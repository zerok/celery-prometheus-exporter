from time import time

import celery
import celery.states
import amqp.exceptions

from celery.events import Event
from celery.utils import uuid
from prometheus_client import REGISTRY
from unittest import TestCase
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from celery_prometheus_exporter import (
    WorkerMonitoringThread, setup_metrics, MonitorThread, EnableEventsThread,
    TASKS,
    QueueLenghtMonitoringThread, QUEUE_LENGTH)

from celery_test_utils import get_celery_app, SampleTask


class TestFallbackSetup(TestCase):
    def test_fallback(self):
        TASKS.labels(state='RUNNING').set(0)
        setup_metrics(None)


class TestMockedCelery(TestCase):
    task = 'my_task'

    def setUp(self):
        self.app = get_celery_app()
        with patch('celery.task.control.inspect.registered_tasks') as tasks:
            tasks.return_value = {'worker1': [self.task]}
            setup_metrics(self.app)  # reset metrics

    def test_initial_metric_values(self):
        self._assert_task_states(celery.states.ALL_STATES, 0)
        assert REGISTRY.get_sample_value('celery_workers') == 0
        assert REGISTRY.get_sample_value('celery_task_latency_count') == 0
        assert REGISTRY.get_sample_value('celery_task_latency_sum') == 0

    def test_workers_count(self):
        assert REGISTRY.get_sample_value('celery_workers') == 0

        with patch.object(self.app.control, 'ping') as mock_ping:
            w = WorkerMonitoringThread(app=self.app)

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
        task_uuid = uuid()
        hostname = 'myhost'
        local_received = time()
        latency_before_started = 123.45
        runtime = 234.5

        m = MonitorThread(app=self.app)

        self._assert_task_states(celery.states.ALL_STATES, 0)
        assert REGISTRY.get_sample_value('celery_task_latency_count') == 0
        assert REGISTRY.get_sample_value('celery_task_latency_sum') == 0

        m._process_event(Event(
            'task-received', uuid=task_uuid,  name=self.task,
            args='()', kwargs='{}', retries=0, eta=None, hostname=hostname,
            clock=0,
            local_received=local_received))
        self._assert_all_states({celery.states.RECEIVED})

        m._process_event(Event(
            'task-started', uuid=task_uuid, hostname=hostname,
            clock=1, name=self.task,
            local_received=local_received + latency_before_started))
        self._assert_all_states({celery.states.STARTED})

        m._process_event(Event(
            'task-succeeded', uuid=task_uuid, result='42',
            runtime=runtime, hostname=hostname, clock=2,
            local_received=local_received + latency_before_started + runtime))
        self._assert_all_states({celery.states.SUCCESS})

        assert REGISTRY.get_sample_value('celery_task_latency_count') == 1
        self.assertAlmostEqual(REGISTRY.get_sample_value(
            'celery_task_latency_sum'), latency_before_started)
        assert REGISTRY.get_sample_value(
            'celery_tasks_runtime_seconds_count',
            labels=dict(name=self.task)) == 1
        assert REGISTRY.get_sample_value(
            'celery_tasks_runtime_seconds_sum',
            labels=dict(name=self.task)) == 234.5

    def test_enable_events(self):
        with patch.object(
                self.app.control, 'enable_events') as mock_enable_events:
            e = EnableEventsThread(app=self.app)
            e.enable_events()
            mock_enable_events.assert_called_once_with()

    def test_can_measure_queue_length(self):
        celery_app = get_celery_app(queue='realqueue')
        sample_task = SampleTask()
        sample_task.app = celery_app
        monitoring_thread_instance = QueueLenghtMonitoringThread(celery_app, queue_list=['realqueue'])

        sample_task.delay()
        monitoring_thread_instance.measure_queues_length()
        sample = REGISTRY.get_sample_value('celery_queue_length', {'queue_name':'realqueue'})

        self.assertEqual(1.0, sample)

    def test_set_zero_on_queue_length_when_an_channel_layer_error_occurs_during_queue_read(self):
        instance = QueueLenghtMonitoringThread(app=self.app, queue_list=['noqueue'])

        instance.measure_queues_length()
        sample = REGISTRY.get_sample_value('celery_queue_length', {'queue_name':'noqueue'})

        self.assertEqual(0.0, sample)

    def _assert_task_states(self, states, cnt):
        for state in states:
            assert REGISTRY.get_sample_value(
                'celery_tasks', labels=dict(state=state)) == cnt
            task_by_name_label = dict(state=state, name=self.task)
            assert REGISTRY.get_sample_value(
                'celery_tasks_by_name', labels=task_by_name_label) == cnt

    def _assert_all_states(self, exclude):
        self._assert_task_states(celery.states.ALL_STATES - exclude, 0)
        self._assert_task_states(exclude, 1)

    def _setup_task_with_celery_and_queue_support(self, queue_name, task, celery_app):
        task.app = celery_app

        return task
