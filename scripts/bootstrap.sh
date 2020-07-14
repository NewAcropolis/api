#!/bin/bash
if [ ! -d "env" ]; then
    virtualenv -p python3 env
fi

if [ -z "$VIRTUAL_ENV" ] && [ -d env ]; then
  echo 'activate env'
  source ./env/bin/activate
fi

pip install -r requirements_tests.txt
pip install google-cloud-logging==1.11.0
