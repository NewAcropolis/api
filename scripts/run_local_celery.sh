# ps auxww | grep "run_celery.celery worker" | awk '{print $2}' | xargs kill -9
ps auxww | grep "rq cron" | awk '{print $2}' | xargs kill -9
ps auxww | grep "rq worker" | awk '{print $2}' | xargs kill -9
ps auxww | grep "run_celery.celery beat" | awk '{print $2}' | xargs kill -9
rm celerybeat.pid
# watchmedo auto-restart --directory=./app --pattern=*.py --recursive -- celery -A run_celery.celery beat &
watchmedo auto-restart --directory=./app --pattern=*.py --recursive -- rq cron rq_cron.py &
watchmedo auto-restart --directory=./app --pattern=*.py --recursive -- rq worker --with-scheduler &
watchmedo auto-restart --directory=./app --pattern=*.py --recursive -- celery -A run_celery.celery worker -n worker-development --loglevel=INFO --concurrency=1 --pool=solo
