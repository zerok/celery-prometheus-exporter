import io

from setuptools import setup


long_description = "See https://github.com/zerok/celery-prometheus-exporter"
with io.open('README.rst', encoding='utf-8') as fp:
    long_description = fp.read()

setup(
    name='celery-prometheus-exporter',
    description="Simple Prometheus metrics exporter for Celery",
    long_description=long_description,
    version='1.0.1',
    author='Horst Gutmann',
    license='MIT',
    author_email='horst@zerokspot.com',
    url='https://github.com/zerok/celery-prometheus-exporter',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
    ],
    py_modules=[
        'celery_prometheus_exporter',
    ],
    install_requires=[
        'celery>=3',
        'prometheus_client',
    ],
    entry_points={
        'console_scripts': [
            'celery-prometheus-exporter = celery_prometheus_exporter:main',
        ],
    }
)
