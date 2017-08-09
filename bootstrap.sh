#!/bin/bash
if [ ! -d "venv" ]; then
    virtualenv venv
fi

if [ -z "$VIRTUAL_ENV" ] && [ -d venv ]; then
  . ./venv/bin/activate
fi

pip install -r requirements.txt
