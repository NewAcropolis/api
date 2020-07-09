#!/bin/bash
if [ ! -d "env" ]; then
    python3 -m venv env
fi

if [ -z "$VIRTUAL_ENV" ] && [ -d env ]; then
  echo 'activate env'
  source ./env/bin/activate
fi

pip install -r requirements_tests.txt
pip install google-cloud-logging==1.11.0
