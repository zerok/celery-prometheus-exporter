celery_exporter.img: celery_prometheus_exporter.py Dockerfile requirements.txt
	docker build -t celery_exporter .
	docker save -o $@ celery_exporter:latest

.PHONY: clean
clean:
	rm -f celery_exporter.img
