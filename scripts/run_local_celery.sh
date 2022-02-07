ps auxww | grep "run_celery.celery worker" | awk '{print $2}' | xargs kill -9
ps auxww | grep "run_celery.celery beat" | awk '{print $2}' | xargs kill -9
rm celerybeat.pid
watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A run_celery.celery beat &
watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A run_celery.celery worker -n worker-development --loglevel=INFO --concurrency=1
