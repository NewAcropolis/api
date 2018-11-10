# New Acropolis UK API  [![Build Status](https://travis-ci.org/NewAcropolis/api.svg?branch=master)](https://travis-ci.org/NewAcropolis/api)
[![Coverage Status](https://coveralls.io/repos/github/NewAcropolis/api/badge.svg?branch=master)](https://coveralls.io/github/NewAcropolis/api?branch=master)

## Create virtualenv

A Virtual Environment is an isolated working copy of Python which
allows you to work on a specific project without worry of affecting other projects

Follow this guide to set up your virtualenv for this project;
https://virtualenvwrapper.readthedocs.io/en/latest/

## Using Makefile

Run `make dependencies` to install dependencies

Run `Make` to list available commands

## Set up environment variables

Copy `environment_sample.sh` and create an `environment.sh` file and fill in the env vars

```
env_variables:
  export DATABASE_URL_development=<postgres url>
  export ADMIN_CLIENT_ID=<admin client id>
  export ADMIN_PASSWORD=<admin client password>
  export ADMIN_CLIENT_SECRET=<admin client secret>
  export JWT_SECRET=<secret key>
```

Run `source environment.sh` to make the parameters available

## Running tests

On project path -

```shell
./scripts/run_tests.sh
```

## Run integration tests

Run the api `make run`

While the application is running, run the `./integration_test.sh`

## Starting the web application

On project path -

```shell
./scripts/run_app.sh [ENV]
```

Where ENV is -

`development - port 5000`
`https://<new acropolis url>/dev/`

`preview - port 4000`
`https://<new acropolis url>/preview/`

`live - port 8000`
`https://<new acropolis url>/`

## Logging

Logs are stored under the `logs` folder
