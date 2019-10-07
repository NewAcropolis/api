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
  nooutput=' >&- 2>&- <&- &'
fi

pip install flower==0.9.3

# kill existing celery workers
ps auxww | grep "celery worker-$ENV" | awk '{print $2}' | xargs kill -9

if [ -f "celerybeat.pid" ]; then
  kill -9 `cat celerybeat.pid` && rm celerybeat.pid
fi

# kill flower
lsof -i :$FLOWER_PORT  | awk '{if(NR>1)print $2}' | xargs kill -9

eval "celery -A run_celery.celery worker --loglevel=INFO -n worker-$ENV --concurrency=1"$nooutput
eval "celery -A run_celery.celery flower --url_prefix=celery --address=127.0.0.1 --port=$FLOWER_PORT"$nooutput
eval "celery -A run_celery.celery beat --loglevel=DEBUG"$nooutput
