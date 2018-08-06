all: celery_exporter-celery3.img celery_exporter-celery4.img

celery_exporter-celery3.img: celery_prometheus_exporter.py Dockerfile-celery3 requirements/*
	docker build -f Dockerfile-celery3 -t celery_exporter:1-celery3 .
	docker save -o $@ celery_exporter:1-celery3

celery_exporter-celery4.img: celery_prometheus_exporter.py Dockerfile-celery4 requirements/*
	docker build -f Dockerfile-celery4 -t celery_exporter:1-celery4 .
	docker save -o $@ celery_exporter:1-celery4

.PHONY: clean all
clean:
	rm -rf celery_exporter.img *.egg-info build dist

publish: all
	docker tag celery_exporter:1-celery3 zerok/celery_exporter:1-celery3
	docker tag celery_exporter:1-celery3 zerok/celery_exporter:1.3.0-celery3
	docker tag celery_exporter:1-celery4 zerok/celery_exporter:1-celery4
	docker tag celery_exporter:1-celery4 zerok/celery_exporter:1.3.0-celery4
	docker push zerok/celery_exporter:1-celery4
	docker push zerok/celery_exporter:1.3.0-celery4
	docker push zerok/celery_exporter:1-celery3
	docker push zerok/celery_exporter:1.3.0-celery3
