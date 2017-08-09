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
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class Development(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    PORT = 5000
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL_development')


class Preview(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    PORT = 4000
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL_preview')


class Live(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    PORT = 8000
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL_live')


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
