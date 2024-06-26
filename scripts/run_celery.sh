#!/bin/bash
set +ex

ENV=development

if [ ! -z "$1" ]; then
    ENV=$1
fi

if [ -z "$VIRTUAL_ENV" ] && [ -d env ]; then
  echo 'activate env for celery'
  source ./env/bin/activate
fi

logoutput=" >>/var/log/na-api/celery-$ENV.log 2>&1 &"

# kill existing celery workers
ps auxww | grep "celery worker -n worker-$ENV" | awk '{print $2}' | xargs kill -9
ps auxww | grep "run_celery.celery beat" | awk '{print $2}' | xargs kill -9

# give time for workers to shutdown
sleep 10

if [ -f "celerybeat.pid" ]; then
  kill -9 `cat celerybeat.pid` && rm celerybeat.pid
fi

eval "celery -A run_celery.celery worker -n worker-$ENV --loglevel=INFO --concurrency=1"$logoutput
eval "celery -A run_celery.celery beat"$logoutput

# check that celery has started properly
num_workers=$(( $(ps auxww | grep "celery worker -n worker-$ENV" | wc -l) -1))
echo "Running $num_workers workers"

num_beat_workers=$(( $(ps auxww | grep "celery beat" | wc -l) -1))
echo "Running $num_beat_workers beat workers"

[ $num_workers > 0 -a $num_beat_workers > 0 ] && echo 'celery running with correct number of workers' || echo 'ERROR: incorrect number of celery workers'
