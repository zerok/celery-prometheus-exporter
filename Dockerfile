FROM python:3.5-alpine
MAINTAINER Horst Gutmann <horst@zerokspot.com>

RUN mkdir /app
ADD celery_prometheus_exporter.py docker-entrypoint.sh requirements.txt /app/
WORKDIR /app

ENV PYTHONUNBUFFERED 1
RUN pip install -r requirements.txt
ENTRYPOINT ["/bin/sh", "/app/docker-entrypoint.sh"]
CMD []

EXPOSE 8888
