#!/bin/bash
set +ex

ENV=development
www_dir="www-$ENV"

port=5000

if [ ! -z "$1" ]; then
    ENV=$1

    if [ "$ENV" = "gunicorn" ]; then
      ENV=development
    fi

    www_dir="www-$ENV"
    port="$(python app/config.py -e $ENV)"
fi

# kill any existing services running on port
sudo kill `sudo lsof -t -i:$port`

echo "hosting on $www_dir"

DATABASE_URL_ENV="\${DATABASE_URL_$ENV}"

eval "DATABASE_URL=$DATABASE_URL_ENV"

if psql -lqt "${DATABASE_URL}" | cut -d \| -f 1 | grep -qw ${DATABASE_URL##*/}; then
  echo ${DATABASE_URL##*/} 'already exists'
else
  createdb ${DATABASE_URL##*/}
  echo ${DATABASE_URL##*/} 'created'
fi

if [ -z "$VIRTUAL_ENV" ] && [ -d venv ]; then
  echo 'activate venv'
  source ./venv/bin/activate
fi

if [ -z "$TRAVIS_COMMIT" ]; then
  export TRAVIS_COMMIT=$(git rev-parse HEAD)
fi

python app_start.py db upgrade

if [ "$2" = "gunicorn" -o "$1" = "gunicorn" ]; then
  export APP_SERVER=gunicorn
  NAME="na_api"
  FLASKDIR=app
  SOCKFILE=sock
  USER=root
  GROUP=root
  NUM_WORKERS=3
  TIMEOUT=240
  
  echo "Starting $NAME"
  
  # Create the run directory if it doesn't exist
  RUNDIR=$(dirname $SOCKFILE)
  test -d $RUNDIR || mkdir -p $RUNDIR
  
  # Start your gunicorn
  exec gunicorn wsgi -b 0.0.0.0:$port \
    --access-logfile logs/gunicorn.log \
    --error-logfile logs/gunicorn.error.log \
    --name $NAME \
    --timeout $TIMEOUT \
    --workers $NUM_WORKERS \
    --log-level DEBUG \
    --reload \
    --worker-class gevent \
    --pid /tmp/gunicorn-$ENV.pid
    # --user=$USER --group=$GROUP \
    # --bind=unix:$SOCKFILE
else
  export APP_SERVER=flask
  python app_start.py runserver --port $port

  if [ $www_dir != "www" ]; then
      echo "running on " $ENV
      exit 0
  fi
fi
