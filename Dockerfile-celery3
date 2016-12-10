FROM python:3.5-alpine
MAINTAINER Horst Gutmann <horst@zerokspot.com>

RUN mkdir -p /app/requirements
ADD requirements/* /app/requirements/
WORKDIR /app

ENV PYTHONUNBUFFERED 1
RUN pip install -r requirements/celery3.txt
ADD celery_prometheus_exporter.py docker-entrypoint.sh /app/
ENTRYPOINT ["/bin/sh", "/app/docker-entrypoint.sh"]
CMD []

EXPOSE 8888
