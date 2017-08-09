#!/bin/bash
set +e

ENV=development
www_dir="www-$ENV"

port=5000

if [ ! -z "$1" ]; then
    www_dir="www-$1"
    cd $www_dir
    port="$(python app/config.py -e $1)"

    # kill any existing services running on port
    fuser -k -n tcp $port

    ENV=$1
fi

echo "hosting on $www_dir"

DATABASE_URL_ENV="\${DATABASE_URL_$ENV}"

eval "DATABASE_URL=$DATABASE_URL_ENV"

if psql -lqt | cut -d \| -f 1 | grep -qw ${DATABASE_URL##*/}; then
  echo ${DATABASE_URL##*/} 'already exists'
else
  createdb ${DATABASE_URL##*/}
  echo ${DATABASE_URL##*/} 'created'
fi

python app.py db upgrade

if [ $www_dir != "www" ]; then
    python app.py runserver --port $port&
else
    python app.py runserver --port $port
fi

if [ $www_dir != "www" ]; then
    exit 0
fi
