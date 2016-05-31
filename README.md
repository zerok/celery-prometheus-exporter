**Warning:** This is still experimental!

celery-prometheus-exporter is a little exporter for Celery related metrics in
order to get picked up by Prometheus.

So far it provides access to the following metrics:

* `celery_tasks` exposes the number of tasks currently known to the queue
  seperated by `state` (RUNNING, STARTED, ...).
* `celery_workers` exposes the number of currently probably alive workers


## How to use

At this point this isn't available on PyPI as the code is still very much
work-in-progress and in flux. For this reason the only way to use this is to
check the code out and run with it.

```
$ python main.py
Starting HTTPD on 0.0.0.0:8888
```

If you want the HTTPD to listen to another port, use the `--addr` option.

By default, this will expect the broker to be available through
`redis://redis:6379/0`. If you're using AMQP or something else other than Redis,
take a look at the Celery documentation and install the additioinal requirements
😊 Also use the `--broker` option to specify a different broker URL.

There is also a Dockerfile and a Makefile available which you should be able to
use out of the box to get this going with Docker. The image exposes port 8888.

If you then look at the exposed metrics, you should see something like this:

```
$ http get http://localhost:8888/metrics | grep celery_
# HELP celery_workers Number of alive workers
# TYPE celery_workers gauge
celery_workers 1.0
# HELP celery_tasks Number of tasks per state
# TYPE celery_tasks gauge
celery_tasks{state="PENDING"} 0.0
celery_tasks{state="STARTED"} 0.0
celery_tasks{state="SUCCESS"} 0.0
celery_tasks{state="FAILURE"} 0.0
celery_tasks{state="RECEIVED"} 0.0
celery_tasks{state="REVOKED"} 0.0
celery_tasks{state="RETRY"} 0.0
```
