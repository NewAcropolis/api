#!/usr/bin/python

import json
import sys
import argparse
import os


def parse_args():  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--env", default="development", help="environment")
    return parser.parse_args()


def output(stmt):  # pragma: no cover
    print(stmt)


def main(argv):
    args = parse_args()

    try:
        output(configs[args.env].PORT)
    except:
        output('No environment')


class Config(object):
    DEBUG = False
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    ADMIN_CLIENT_ID = os.environ.get('ADMIN_CLIENT_ID')
    ADMIN_CLIENT_SECRET = os.environ.get('ADMIN_CLIENT_SECRET')
    TOKEN_EXPIRY = os.environ.get('TOKEN_EXPIRY', 60 * 24)  # expires every 24 hours
    APP_SERVER = os.environ.get('APP_SERVER')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET')
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    ADMIN_USERS = os.environ.get('ADMIN_USERS')
    EMAIL_DOMAIN = os.environ.get('EMAIL_DOMAIN')
    EVENTS_MAX = 30
    PROJECT = os.environ.get('PROJECT')
    STORAGE = os.environ.get('GOOGLE_STORE')
    PAYPAL_URL = os.environ.get('PAYPAL_URL')
    PAYPAL_USER = os.environ.get('PAYPAL_USER')
    PAYPAL_PASSWORD = os.environ.get('PAYPAL_PASSWORD')
    PAYPAL_RECEIVER = os.environ.get('PAYPAL_RECEIVER')
    PAYPAL_SIG = os.environ.get('PAYPAL_SIG')
    PAYPAL_VERIFY_URL = os.environ.get('PAYPAL_VERIFY_URL')
    EMAIL_PROVIDER_URL = os.environ.get('EMAIL_PROVIDER_URL')
    EMAIL_PROVIDER_APIKEY = os.environ.get('EMAIL_PROVIDER_APIKEY')
    EMAIL_TOKENS = json.loads(os.environ.get('EMAIL_TOKENS')) if 'EMAIL_TOKENS' \
        in os.environ and os.environ.get('EMAIL_TOKENS')[:1] == '{' else {}
    EMAIL_SALT = os.environ.get('EMAIL_SALT')
    EMAIL_UNSUB_SALT = os.environ.get('EMAIL_UNSUB_SALT')
    TEST_EMAIL = os.environ.get('TEST_EMAIL')
    FRONTEND_ADMIN_URL = os.environ.get('FRONTEND_ADMIN_URL')
    API_BASE_URL = os.environ.get('API_BASE_URL')
    IMAGES_URL = os.environ.get('IMAGES_URL')
    FRONTEND_URL = os.environ.get('FRONTEND_URL')
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    TRAVIS_COMMIT = os.environ.get('TRAVIS_COMMIT')

    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
    # CELERY_TASK_RESULT_EXPIRES = 30
    CELERY_TIMEZONE = 'Europe/London'
    CELERY_ENABLE_UTC = True
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'

    EMAIL_DELAY = 60
    EMAIL_LIMIT = 400


class Development(Config):
    DEBUG = True
    ENVIRONMENT = 'development'
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    PORT = 5000
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL_development')
    STORAGE = '{}development'.format(os.environ.get('GOOGLE_STORE'))


class Preview(Config):
    DEBUG = True
    ENVIRONMENT = 'preview'
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    PORT = 4000
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL_preview')
    STORAGE = '{}preview'.format(os.environ.get('GOOGLE_STORE'))


class Live(Config):
    DEBUG = True
    ENVIRONMENT = 'live'
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    PORT = 8000
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL_live')
    STORAGE = '{}live'.format(os.environ.get('GOOGLE_STORE'))


configs = {
    'development': Development,
    # 'test': Test,
    'preview': Preview,
    # 'staging': Staging,
    'live': Live,
    # 'production': Live
}


if __name__ == '__main__':  # pragma: no cover
    main(sys.argv[1:])
