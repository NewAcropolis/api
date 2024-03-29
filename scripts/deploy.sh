#!/bin/bash
set +ex

if [ -z "$environment" ]; then
    if [ ! -z "$1" ]; then
        environment=$1
    else
        echo "*** set environment as preview ***"
        environment=preview
    fi
fi 

if [ -z $GITHUB_ACTIONS ]; then
    source $environment-environment.sh
    src=.
else 
    src="$GITHUB_WORKSPACE"

    eval "GOOGLE_APPLICATION_CREDENTIALS=\$GOOGLE_APPLICATION_CREDENTIALS_$environment"
    eval "DEPLOY_KEY=\${DEPLOY_KEY_$environment}"
    eval "deploy_host=\${deploy_host_$environment}"
    eval "user=\${user_$environment}"

    echo $DEPLOY_KEY | base64 --decode > deploy_rsa

    eval "$(ssh-agent)"
    chmod 600 deploy_rsa
    ssh-add deploy_rsa
fi

if [ -z $debug ]; then
    output_params=">&- 2>&- <&- &"
    celery_output_params=">&- 2>&- <&- &"
else
    output_params="&>> /var/log/na-api/$environment.log"
    celery_output_params="&>> /var/log/na-api/celery-$environment.log"
fi

port="$(python $src/app/config.py -e $environment)"
if [ $port != 'No environment' ]; then
    rsync -ravzhe "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" $src/ --exclude-from "$src/.exclude" --quiet $user@$deploy_host:www-$environment/
    eval "DATABASE_URL_ENV=\${DATABASE_URL_$environment}"
    eval "ADMIN_CLIENT_ID=\${ADMIN_CLIENT_ID_$environment}"
    eval "ADMIN_CLIENT_SECRET=\${ADMIN_CLIENT_SECRET_$environment}"
    eval "ADMIN_USERS=\${ADMIN_USERS_$environment}"
    eval "PAYPAL_URL=\${PAYPAL_URL_$environment}"
    eval "PAYPAL_USER=\${PAYPAL_USER_$environment}"
    eval "PAYPAL_PASSWORD=\${PAYPAL_PASSWORD_$environment}"
    eval "PAYPAL_SIG=\${PAYPAL_SIG_$environment}"
    eval "PAYPAL_RECEIVER=\${PAYPAL_RECEIVER_$environment}"
    eval "PAYPAL_VERIFY_URL=\${PAYPAL_VERIFY_URL_$environment}"
    eval "EMAIL_PROVIDER_URL=\${EMAIL_PROVIDER_URL_$environment}"
    eval "EMAIL_PROVIDER_APIKEY=\${EMAIL_PROVIDER_APIKEY_$environment}"
    eval "EMAIL_TOKENS=\$EMAIL_TOKENS"
    eval "EMAIL_ANYTIME=\$EMAIL_ANYTIME"
    eval "EMAIL_SALT=\$EMAIL_SALT_$environment"
    eval "EMAIL_UNSUB_SALT=\$EMAIL_UNSUB_SALT_$environment"
    eval "TEST_EMAIL=\$TEST_EMAIL_$environment"
    eval "EMAIL_DISABLED=\$EMAIL_DISABLED_$environment"
    eval "EMAIL_RESTRICT=\$EMAIL_RESTRICT_$environment"
    eval "FRONTEND_ADMIN_URL=\${FRONTEND_ADMIN_URL_$environment}"
    eval "API_BASE_URL=\$API_BASE_URL_$environment"
    eval "FRONTEND_URL=\$FRONTEND_URL_$environment"
    eval "IMAGES_URL=\$IMAGES_URL_$environment"
    eval "CELERY_BROKER_URL=\$CELERY_BROKER_URL_$environment"
    eval "PROJECT=\$PROJECT_$environment"
    eval "GOOGLE_AUTH_USER=\$GOOGLE_AUTH_USER_$environment"
    eval "JWT_SECRET=\$JWT_SECRET_$environment"
    eval "GA_ID=\$GA_ID_$environment"
    eval "INSTAGRAM_URL=\$INSTAGRAM_URL"
    eval "RESTART_CELERY=\$RESTART_CELERY"
    eval "GOOGLE_APPLICATION_CREDENTIALS=\$GOOGLE_APPLICATION_CREDENTIALS_$environment"
    eval "SMTP_SERVER=\$SMTP_SERVER"
    eval "SMTP_USER=\$SMTP_USER_$environment"
    eval "SMTP_PASS=\$SMTP_PASS_$environment"
    
    echo starting app $environment on port $port
    if [ $environment = 'live' -o $environment = 'preview' ]; then
        ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $user@$deploy_host """
cat >/home/$user/www-$environment/na-api.env << \EOL
ENVIRONMENT=$environment
DATABASE_URL_$environment=$DATABASE_URL_ENV
ADMIN_CLIENT_ID=$ADMIN_CLIENT_ID
ADMIN_CLIENT_SECRET=$ADMIN_CLIENT_SECRET
JWT_SECRET=$JWT_SECRET
PROJECT=$PROJECT
GOOGLE_STORE=$GOOGLE_STORE
ADMIN_USERS=$ADMIN_USERS
EMAIL_DOMAIN=$EMAIL_DOMAIN
PAYPAL_URL=$PAYPAL_URL
PAYPAL_USER=$PAYPAL_USER
PAYPAL_PASSWORD=$PAYPAL_PASSWORD
PAYPAL_SIG=$PAYPAL_SIG
PAYPAL_RECEIVER=$PAYPAL_RECEIVER
PAYPAL_VERIFY_URL=$PAYPAL_VERIFY_URL
EMAIL_PROVIDER_URL=$EMAIL_PROVIDER_URL
EMAIL_PROVIDER_APIKEY=$EMAIL_PROVIDER_APIKEY
EMAIL_TOKENS=$EMAIL_TOKENS
EMAIL_ANYTIME=$EMAIL_ANYTIME
EMAIL_SALT=$EMAIL_SALT
EMAIL_UNSUB_SALT=$EMAIL_UNSUB_SALT
TEST_EMAIL=$TEST_EMAIL
EMAIL_DISABLED=$EMAIL_DISABLED
EMAIL_RESTRICT=$EMAIL_RESTRICT
FRONTEND_ADMIN_URL=$FRONTEND_ADMIN_URL
API_BASE_URL=$API_BASE_URL
FRONTEND_URL=$FRONTEND_URL
IMAGES_URL=$IMAGES_URL
GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS
GITHUB_SHA=$GITHUB_SHA
CELERY_BROKER_URL=$CELERY_BROKER_URL
RESTART_CELERY=$RESTART_CELERY
GA_ID=$GA_ID
INSTAGRAM_URL="$INSTAGRAM_URL"
SMTP_SERVER=$SMTP_SERVER
SMTP_USER=$SMTP_USER
SMTP_PASS=$SMTP_PASS
TEST_VERIFY=$TEST_VERIFY
EOL

sudo systemctl daemon-reload
sudo systemctl restart na-api.service

cd www-$environment
set -a
. ./env/bin/activate && . ./na-api.env && ./scripts/run_celery.sh $environment $celery_output_params
set +a
        """
    else
        ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $user@$deploy_host """
        cd www-$environment
        export ENVIRONMENT=$environment
        export DATABASE_URL_$environment=$DATABASE_URL_ENV
        export ADMIN_CLIENT_ID=$ADMIN_CLIENT_ID
        export ADMIN_CLIENT_SECRET=$ADMIN_CLIENT_SECRET
        export JWT_SECRET=$JWT_SECRET
        export PROJECT=$PROJECT
        export GOOGLE_STORE=$GOOGLE_STORE
        export ADMIN_USERS=$ADMIN_USERS
        export EMAIL_DOMAIN=$EMAIL_DOMAIN
        export PAYPAL_URL=$PAYPAL_URL
        export PAYPAL_USER=$PAYPAL_USER
        export PAYPAL_PASSWORD=$PAYPAL_PASSWORD
        export PAYPAL_SIG=$PAYPAL_SIG
        export PAYPAL_RECEIVER=$PAYPAL_RECEIVER
        export PAYPAL_VERIFY_URL=$PAYPAL_VERIFY_URL
        export EMAIL_PROVIDER_URL=$EMAIL_PROVIDER_URL
        export EMAIL_PROVIDER_APIKEY=$EMAIL_PROVIDER_APIKEY
        export EMAIL_TOKENS=$EMAIL_TOKENS
        export EMAIL_ANYTIME=$EMAIL_ANYTIME
        export EMAIL_SALT=$EMAIL_SALT
        export EMAIL_UNSUB_SALT=$EMAIL_UNSUB_SALT
        export TEST_EMAIL=$TEST_EMAIL
        export EMAIL_DISABLED=$EMAIL_DISABLED
        export EMAIL_RESTRICT=$EMAIL_RESTRICT
        export FRONTEND_ADMIN_URL=$FRONTEND_ADMIN_URL
        export API_BASE_URL=$API_BASE_URL
        export FRONTEND_URL=$FRONTEND_URL
        export GA_ID=$GA_ID
        export INSTAGRAM_URL="$INSTAGRAM_URL"
        export IMAGES_URL=$IMAGES_URL
        export GITHUB_SHA=$GITHUB_SHA
        export CELERY_BROKER_URL=$CELERY_BROKER_URL
        export RESTART_CELERY=$RESTART_CELERY
        export SMTP_SERVER=$SMTP_SERVER
        export SMTP_USER=$SMTP_USER
        export SMTP_PASS=$SMTP_PASS
        export TEST_VERIFY=$TEST_VERIFY
        export GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS

        ./scripts/bootstrap.sh
        if [ -z "$RESTART_CELERY" ]; then
            ./scripts/run_app.sh $environment gunicorn $output_params
        fi
        ./scripts/run_celery.sh $environment $celery_output_params
        """
    fi

    if [ -z "$RESTART_CELERY" ]; then
       source ./scripts/check_site.sh $deploy_host:$port
    fi
else
    echo "$port"
    exit 1
fi
