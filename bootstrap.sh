#!/bin/bash
if [ ! -d "venv" ]; then
    virtualenv venv
fi

if [ -z "$VIRTUAL_ENV" ] && [ -d venv ]; then
  source ./venv/bin/activate
fi

if [ -z "$1" ]; then
  ENV=development
else 
  ENV=$1
fi

pip install -r requirements.txt

DATABASE_URL_ENV="\${DATABASE_URL_$ENV}"

eval "DATABASE_URL=$DATABASE_URL_ENV"

if psql -lqt | cut -d \| -f 1 | grep -qw ${DATABASE_URL##*/}; then
  echo ${DATABASE_URL##*/} 'already exists'
else
  createdb ${DATABASE_URL##*/}
  echo ${DATABASE_URL##*/} 'created'
fi

python app.py db upgrade
