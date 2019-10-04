#!/bin/bash
set +x

ENV=development

if [ ! -z "$1" ]; then
    ENV=$1
fi

if [ "$ENV" = 'preview' ]; then
    PORT=4555
else
    PORT=5555
fi

if [ -z "$VIRTUAL_ENV" ] && [ -d venv ]; then
  echo 'activate venv for celery'
  source ./venv/bin/activate
  nooutput=' >&- 2>&- <&- &'
fi

pip install flower==0.9.3

# kill existing celery workers
ps auxww | grep "celery worker-$ENV" | awk '{print $2}' | xargs kill -9

# kill flower
lsof -i :$PORT  | awk '{if(NR>1)print $2}' | xargs kill -9

FLOWER_BASIC_AUTH=admin:test

eval "celery -A run_celery.celery worker --loglevel=INFO -n worker-$ENV@%h --concurrency=1"$nooutput
eval "celery -A run_celery.celery flower --url_prefix=celery --address=127.0.0.1 --port=$PORT"$nooutput
