from setuptools import setup


setup(
    name='celery-prometheus-exporter',
    version='1.0.0',
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
        'celery>=3,<4',
        'prometheus_client',
    ],
    entry_points={
        'console_scripts': [
            'celery-prometheus-exporter = celery_prometheus_exporter:main',
        ],
    }
)
