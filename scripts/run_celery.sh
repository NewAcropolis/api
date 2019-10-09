#!/bin/bash
set +ex

ENV=development

if [ ! -z "$1" ]; then
    ENV=$1
fi

if [ "$ENV" = 'preview' ]; then
    FLOWER_PORT=4555
else
    FLOWER_PORT=5555
fi

if [ -z "$VIRTUAL_ENV" ] && [ -d venv ]; then
  echo 'activate venv for celery'
  source ./venv/bin/activate
fi

logoutput=" >>/var/log/na-api/celery-$ENV.log 2>&1 &"

pip install flower==0.9.3

# kill existing celery workers
ps auxww | grep "celery worker -n worker-$ENV" | awk '{print $2}' | xargs kill -9

if [ -f "celerybeat.pid" ]; then
  kill -9 `cat celerybeat.pid` && rm celerybeat.pid && sleep 10
fi

# kill flower
FLOWER_PID=lsof -i :$FLOWER_PORT  | awk '{if(NR>1)print $2}'

if [ -z $FLOWER_PID -o $RESTART_FLOWER ]; then
  if [ ! -z $FLOWER_PID ]; then
    kill -9 $FLOWER_PID
  fi
  eval "celery -A run_celery.celery flower --url_prefix=celery --address=127.0.0.1 --port=$FLOWER_PORT"$logoutput
fi

eval "celery -A run_celery.celery worker -n worker-$ENV --loglevel=INFO --concurrency=1"$logoutput
eval "celery -A run_celery.celery beat"$logoutput
