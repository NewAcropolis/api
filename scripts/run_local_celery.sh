watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A run_celery.celery worker -n worker-dev --loglevel=INFO --concurrency=1
