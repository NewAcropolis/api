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
    PAYPAL_RECEIVER_ID = os.environ.get('PAYPAL_RECEIVER_ID')
    PAYPAL_SIG = os.environ.get('PAYPAL_SIG')
    PAYPAL_VERIFY_URL = os.environ.get('PAYPAL_VERIFY_URL')
    EMAIL_TOKENS = json.loads(os.environ.get('EMAIL_TOKENS')) if 'EMAIL_TOKENS' \
        in os.environ and os.environ.get('EMAIL_TOKENS')[:1] == '{' else {}
    EMAIL_SALT = os.environ.get('EMAIL_SALT')
    EMAIL_UNSUB_SALT = os.environ.get('EMAIL_UNSUB_SALT')
    TEST_EMAIL = os.environ.get('TEST_EMAIL')
    FRONTEND_ADMIN_URL = os.environ.get('FRONTEND_ADMIN_URL')
    API_BASE_URL = os.environ.get('API_BASE_URL')
    IMAGES_URL = os.environ.get('IMAGES_URL')
    THUMBNAIL_MAXSIZE = 250, 250
    STANDARD_MAXSIZE = 1500, 800
    FRONTEND_URL = os.environ.get('FRONTEND_URL')
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    GITHUB_SHA = os.environ.get('GITHUB_SHA')

    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
    CELERY_TIMEZONE = 'Europe/London'
    CELERY_ENABLE_UTC = True
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'
    # CELERY_IMPORTS = ("app.na_celery.event_tasks", "app.na_celery.stats_tasks",)
    CELERY_IMPORTS = ("app.na_celery.event_tasks",)

    if not os.environ.get('GITHUB_ACTIONS'):  # pragma: no cover
        from celery.schedules import crontab

        CELERYBEAT_SCHEDULE = {
            'send-event-reminder-email': {
                'task': 'send_event_email_reminder',
                'schedule': crontab(minute=0, hour='10') if ENVIRONMENT != 'development' else crontab(minute='*/10'),
            },
            'send-periodic-emails': {
                'task': 'send_periodic_emails',
                'schedule': crontab(minute=0, hour='*') if ENVIRONMENT != 'development' else crontab(minute='*/10'),
            },
            'send-missing-confirmation-emails': {
                'task': 'send_missing_confirmation_emails',
                'schedule': crontab(minute=0, hour='9') if ENVIRONMENT != 'development' else crontab(minute='*/10'),
            },
            # 'send-num-subscribers-and-social-stats': {
            #     'task': 'send_num_subscribers_and_social_stats',
            #     'schedule': crontab(hour=7, day_of_month=1) \
            #                 if ENVIRONMENT != 'development' else crontab(minute='*/10'),
            # },
        }

    EMAIL_DELAY = 4 if ENVIRONMENT != 'development' else 0  # hours
    EMAIL_LIMIT = 400
    EMAIL_RESTRICT = os.environ.get('EMAIL_RESTRICT') == '1'
    EMAIL_EARLIEST_TIME = "08:00:00"
    EMAIL_LATEST_TIME = "22:00:00"
    EMAIL_ANYTIME = os.environ.get('EMAIL_ANYTIME') == '1'
    EMAIL_DISABLED = os.environ.get('EMAIL_DISABLED')

    GA_ID = os.environ.get('GA_ID')
    DISABLE_STATS = os.environ.get('DISABLE_STATS') == '1'

    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_USER = os.environ.get('SMTP_USER')
    SMTP_PASS = os.environ.get('SMTP_PASS')

    FACEBOOK_URL = "https://www.facebook.com/pg/newacropolisuk/community/"
    INSTAGRAM_URL = os.environ.get('INSTAGRAM_URL')
    POSTAGE_COUNTRY_CODE = "GB"
    TEST_VERIFY = os.environ.get('TEST_VERIFY') == '1'


class Development(Config):
    DEBUG = True
    ENVIRONMENT = 'development'
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    PORT = 5001
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL_development')
    STORAGE = '{}development'.format(os.environ.get('GOOGLE_STORE'))
    EMAIL_LIMIT = 3
    EMAIL_TEST = os.environ.get('EMAIL_TEST')
    PREVIEW_API_BASE_URL = os.environ.get('PREVIEW_API_BASE_URL')


class Preview(Config):
    DEBUG = True
    ENVIRONMENT = 'preview'
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    PORT = 4000
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL_preview')
    STORAGE = '{}preview'.format(os.environ.get('GOOGLE_STORE'))
    EMAIL_LIMIT = 3


class Test(Config):
    DEBUG = True
    ENVIRONMENT = 'test'
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    EMAIL_LIMIT = 3


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
    'test': Test,
    'preview': Preview,
    # 'staging': Staging,
    'live': Live,
    # 'production': Live
}


if __name__ == '__main__':  # pragma: no cover
    main(sys.argv[1:])
