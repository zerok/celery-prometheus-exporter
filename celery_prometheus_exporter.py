import argparse
import celery
import celery.states
import celery.events.state
import collections
import logging
import prometheus_client
import signal
import sys
import threading
import time
import os

__VERSION__ = (1, 1, 0, 'final', 0)


DEFAULT_BROKER = 'redis://redis:6379/0'
DEFAULT_ADDR = '0.0.0.0:8888'

LOG_FORMAT = '[%(asctime)s] %(name)s:%(levelname)s: %(message)s'

TASKS = prometheus_client.Gauge(
    'celery_tasks', 'Number of tasks per state', ['state'])
WORKERS = prometheus_client.Gauge(
    'celery_workers', 'Number of alive workers')
LATENCY = prometheus_client.Histogram(
    'celery_task_latency', 'Seconds between a task is received and started.')


class MonitorThread(threading.Thread):
    """
    MonitorThread is the thread that will collect the data that is later
    exposed from Celery using its eventing system.
    """

    def __init__(self, *args, app=None, **kwargs):
        self._app = app
        self.log = logging.getLogger('monitor')
        super().__init__(*args, **kwargs)

    def run(self):
        self._state = self._app.events.State()
        self._known_states = set()
        self._tasks_started = dict()
        self._monitor()

    def _process_event(self, evt):
        # Events might come in in parallel. Celery already has a lock that deals
        # with this exact situation so we'll use that for now.
        with self._state._mutex:
            if evt['type'].startswith('task-'):
                event_state = evt['type'].split('-').pop()
                state = celery.events.state.TASK_EVENT_TO_STATE[event_state]
                if state == celery.states.STARTED:
                    self._observe_latency(evt)
                self._collect_tasks(evt, state)
            WORKERS.set(len([w for w in self._state.workers.values() if w.alive]))

    def _observe_latency(self, evt):
        try:
            prev_evt = self._state.tasks[evt['uuid']]
        except KeyError:
            pass
        else:
            # ignore latency if it is a retry
            if prev_evt.state == celery.states.RECEIVED:
                LATENCY.observe(evt['local_received'] - prev_evt.local_received)

    def _collect_tasks(self, evt, state):
        if state in celery.states.READY_STATES:
            self._incr_ready_task(evt, state)
        else:
            # add event to list of in-progress tasks
            self._state._event(evt)
        self._collect_unready_tasks()

    def _incr_ready_task(self, evt, state):
        try:
            # remove event from list of in-progress tasks
            self._state.tasks.pop(evt['uuid'])
        except KeyError:
            pass
        TASKS.labels(state).inc()

    def _collect_unready_tasks(self):
        cnt = collections.Counter(
            t.state for _, t in self._state.tasks.items())
        self._known_states.update(cnt.elements())
        seen_states = set()
        for state_name, count in cnt.items():
            TASKS.labels(state_name).set(count)
            seen_states.add(state_name)
        for state_name in self._known_states - seen_states:
            TASKS.labels(state_name).set(0)

    def _monitor(self):
        while True:
            try:
                with self._app.connection() as conn:
                    recv = self._app.events.Receiver(conn, handlers={
                        '*': self._process_event,
                    })
                    recv.capture(limit=None, timeout=None, wakeup=True)
                    self.log.info("Connected to broker")
            except Exception as e:
                self.log.error("Queue connection failed", e)
                setup_metrics()
                time.sleep(5)


class WorkerMonitoringThread(threading.Thread):
    def __init__(self, *args, app=None, **kwargs):
        self._app = app
        super().__init__(*args, **kwargs)

    def run(self):
        while True:
            WORKERS.set(len(self._app.control.ping(timeout=5)))
            time.sleep(5)


def setup_metrics():
    """
    This initializes the available metrics with default values so that
    even before the first event is received, data can be exposed.
    """
    for state in celery.states.ALL_STATES:
        TASKS.labels(state).set(0)
    WORKERS.set(0)


def start_httpd(addr):
    """
    Starts the exposing HTTPD using the addr provided in a seperate
    thread.
    """
    host, port = addr.split(':')
    logging.info('Starting HTTPD on {}:{}'.format(host, port))
    prometheus_client.start_http_server(int(port), host)


def shutdown(signum, frame):
    """
    Shutdown is called if the process receives a TERM signal. This way
    we try to prevent an ugly stacktrace being rendered to the user on
    a normal shutdown.
    """
    logging.info("Shutting down")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--broker', dest='broker', default=DEFAULT_BROKER,
        help="URL to the Celery broker. Defaults to {}".format(DEFAULT_BROKER))
    parser.add_argument(
        '--addr', dest='addr', default=DEFAULT_ADDR,
        help="Address the HTTPD should listen on. Defaults to {}".format(
            DEFAULT_ADDR))
    parser.add_argument(
        '--tz', dest='tz',
        help="Timezone used by the celery app.")
    parser.add_argument(
        '--verbose', action='store_true', default=False,
        help="Enable verbose logging")
    parser.add_argument(
        '--version', action='version', version='.'.join([str(x) for x in __VERSION__]))
    opts = parser.parse_args()

    if opts.verbose:
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    if opts.tz:
        os.environ['TZ'] = opts.tz
        time.tzset()

    setup_metrics()
    app = celery.Celery(broker=opts.broker)
    t = MonitorThread(app=app)
    t.daemon = True
    t.start()
    w = WorkerMonitoringThread(app=app)
    w.daemon = True
    w.start()
    start_httpd(opts.addr)
    t.join()
    w.join()


if __name__ == '__main__':
    main()
