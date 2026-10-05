#!/bin/bash
set +ex

ENV=development
WORKER=celery

if [ ! -z "$1" ]; then
    ENV=$1
fi

if [ ! -z "$2" ]; then
    WORKER=$2
fi

if [ -z "$VIRTUAL_ENV" ] && [ -d env ]; then
  echo "activate env for $WORKER"
  source ./env/bin/activate
fi

if [ "$WORKER" = 'celery' ]; then
  eval "celery -A run_celery.celery worker -n worker-$ENV --loglevel=INFO --concurrency=1 --pool=solo"$logoutput
fi
if [ "$WORKER" = 'rq_cron' ]; then
  eval "rq cron rq_cron.py"
fi
if [ "$WORKER" = 'rq' ]; then
  eval "ENVIRONMENT=$ENV rq worker --with-scheduler"
fi
