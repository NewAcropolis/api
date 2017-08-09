#!/bin/bash
set +x

if [ -z $TRAVIS_BUILD_DIR ]; then
    echo "source environment"
    source environment.sh
    src=.
else 
    src="$TRAVIS_BUILD_DIR"
fi

if [ -z "$environment" ]; then
    echo "set environment as dev"
    environment=development
fi 

port="$(python $src/app/config.py -e $environment)"
if [ $port != 'No environment' ]; then
    rsync -ravzhe "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" $src/ --exclude-from "$src/.exclude" --quiet $user@$deploy_host:www-$environment/
    eval "DATABASE_URL_ENV=\${DATABASE_URL_$environment}"

    echo starting app $environment on port $port
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $user@$deploy_host """
    cd www-$environment
    export DATABASE_URL_$environment=$DATABASE_URL_ENV
    export PGPASSWORD=$PGPASSWORD
    sudo -H sh bootstrap.sh $environment
    sh run_app.sh $environment >&- 2>&- <&- &"""
else
    echo "$port"
    exit 1
fi
