#!/usr/bin/python

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
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
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


class Development(Config):
    DEBUG = True
    ENVIRONMENT = 'development'
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    PORT = 5000
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL_development')
    STORAGE = '{}development'.format(os.environ.get('GOOGLE_STORE'))
    PAYPAL_URL = os.getenv('PAYPAL_URL')
    PAYPAL_USER = os.getenv('PAYPAL_USER')
    PAYPAL_PASSWORD = os.getenv('PAYPAL_PASSWORD')
    PAYPAL_SIG = os.getenv('PAYPAL_SIG')


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
