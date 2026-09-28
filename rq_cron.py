from datetime import timedelta
from os import environ
from rq import cron

from app.na_celery.periodic_tasks import run_periodic_tasks

cron.register(
    run_periodic_tasks,
    queue_name='default',
    interval=int(environ.get('RQ_INTERVAL', timedelta(hours=1).seconds))  # 60 minutes in seconds default
)

print(f"RQ INTERVAL: {environ.get('RQ_INTERVAL')}")
