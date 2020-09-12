watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A run_celery.celery beat &
watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A run_celery.celery worker -n worker-development --loglevel=INFO --concurrency=1
