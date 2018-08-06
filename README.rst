==========================
celery-prometheus-exporter
==========================

.. image:: https://img.shields.io/docker/automated/zerok/celery-prometheus-exporter.svg?maxAge=2592000
    :target: https://hub.docker.com/r/zerok/celery-prometheus-exporter/

celery-prometheus-exporter is a little exporter for Celery related metrics in
order to get picked up by Prometheus. As with other exporters like
mongodb\_exporter or node\_exporter this has been implemented as a
standalone-service to make reuse easier across different frameworks.

So far it provides access to the following metrics:

* ``celery_tasks`` exposes the number of tasks currently known to the queue
  grouped by ``state`` (RECEIVED, STARTED, ...).
* ``celery_tasks_by_name`` exposes the number of tasks currently known to the queue
  grouped by ``name`` and ``state``.
* ``celery_workers`` exposes the number of currently probably alive workers
* ``celery_task_latency`` exposes a histogram of task latency, i.e. the time until
  tasks are picked up by a worker


How to use
==========

There are multiple ways to install this. The obvious one is using ``pip install
celery-prometheus-exporter`` and then using the ``celery-prometheus-exporter``
command::

  $ celery-prometheus-exporter
  Starting HTTPD on 0.0.0.0:8888

This package only depends on Celery directly, so you will have to install
whatever other dependencies you will need for it to speak with your broker 🙂

Celery workers have to be configured to send task-related events:
http://docs.celeryproject.org/en/latest/userguide/configuration.html#worker-send-task-events.

Running ``celery-prometheus-exporter`` with the ``--enable-events`` argument
will periodically enable events on the workers. This is useful because it
allows running celery workers with events disabled, until
``celery-prometheus-exporter`` is deployed, at which time events get enabled
on the workers.

Alternatively, you can use the bundle Makefile and Dockerfile to generate a
Docker image.

By default, the HTTPD will listen at ``0.0.0.0:8888``. If you want the HTTPD
to listen to another port, use the ``--addr`` option or the environment variable
``DEFAULT_ADDR``.

By default, this will expect the broker to be available through
``redis://redis:6379/0``, although you can change via environment variable
``DEFAULT_BROKER``. If you're using AMQP or something else other than
Redis, take a look at the Celery documentation and install the additioinal
requirements 😊 Also use the ``--broker`` option to specify a different broker
URL.

If you need to pass additional options to your broker's transport use the
``--transport-options``  option. It tries to read a dict from a JSON object.
E.g. to set your master name when using Redis Sentinel for broker discovery:
``--transport-options '{"master_name": "mymaster"}'``

Use ``--tz`` to specify the timezone the Celery app is using. Otherwise the
systems local time will be used.


If you then look at the exposed metrics, you should see something like this::

  $ http get http://localhost:8888/metrics | grep celery_
  # HELP celery_workers Number of alive workers
  # TYPE celery_workers gauge
  celery_workers 1.0
  # HELP celery_tasks Number of tasks per state
  # TYPE celery_tasks gauge
  celery_tasks{state="RECEIVED"} 3.0
  celery_tasks{state="PENDING"} 0.0
  celery_tasks{state="STARTED"} 1.0
  celery_tasks{state="RETRY"} 2.0
  celery_tasks{state="FAILURE"} 1.0
  celery_tasks{state="REVOKED"} 0.0
  celery_tasks{state="SUCCESS"} 8.0
  # HELP celery_tasks_by_name Number of tasks per state
  # TYPE celery_tasks_by_name gauge
  celery_tasks_by_name{name="my_app.tasks.calculate_something",state="RECEIVED"} 0.0
  celery_tasks_by_name{name="my_app.tasks.calculate_something",state="PENDING"} 0.0
  celery_tasks_by_name{name="my_app.tasks.calculate_something",state="STARTED"} 0.0
  celery_tasks_by_name{name="my_app.tasks.calculate_something",state="RETRY"} 0.0
  celery_tasks_by_name{name="my_app.tasks.calculate_something",state="FAILURE"} 0.0
  celery_tasks_by_name{name="my_app.tasks.calculate_something",state="REVOKED"} 0.0
  celery_tasks_by_name{name="my_app.tasks.calculate_something",state="SUCCESS"} 1.0
  celery_tasks_by_name{name="my_app.tasks.fetch_some_data",state="RECEIVED"} 3.0
  celery_tasks_by_name{name="my_app.tasks.fetch_some_data",state="PENDING"} 0.0
  celery_tasks_by_name{name="my_app.tasks.fetch_some_data",state="STARTED"} 1.0
  celery_tasks_by_name{name="my_app.tasks.fetch_some_data",state="RETRY"} 2.0
  celery_tasks_by_name{name="my_app.tasks.fetch_some_data",state="FAILURE"} 1.0
  celery_tasks_by_name{name="my_app.tasks.fetch_some_data",state="REVOKED"} 0.0
  celery_tasks_by_name{name="my_app.tasks.fetch_some_data",state="SUCCESS"} 7.0
  # HELP celery_task_latency Seconds between a task is received and started.
  # TYPE celery_task_latency histogram
  celery_task_latency_bucket{le="0.005"} 2.0
  celery_task_latency_bucket{le="0.01"} 3.0
  celery_task_latency_bucket{le="0.025"} 4.0
  celery_task_latency_bucket{le="0.05"} 4.0
  celery_task_latency_bucket{le="0.075"} 5.0
  celery_task_latency_bucket{le="0.1"} 5.0
  celery_task_latency_bucket{le="0.25"} 5.0
  celery_task_latency_bucket{le="0.5"} 5.0
  celery_task_latency_bucket{le="0.75"} 5.0
  celery_task_latency_bucket{le="1.0"} 5.0
  celery_task_latency_bucket{le="2.5"} 8.0
  celery_task_latency_bucket{le="5.0"} 11.0
  celery_task_latency_bucket{le="7.5"} 11.0
  celery_task_latency_bucket{le="10.0"} 11.0
  celery_task_latency_bucket{le="+Inf"} 11.0
  celery_task_latency_count 11.0
  celery_task_latency_sum 16.478713035583496


Limitations
===========

* Among tons of other features celery-prometheus-exporter doesn't support stats
  for multiple queues. As far as I can tell, only the routing key is exposed
  through the events API which might be enough to figure out the final queue,
  though.
* This has only been tested with Redis so far.
