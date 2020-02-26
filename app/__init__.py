import os
import logging
import sys
from logging.handlers import RotatingFileHandler

import jinja2
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

from app.na_celery import NewAcropolisCelery

LOG_FORMAT = "{} %(asctime)s;[%(process)d];%(levelname)s;%(message)s"


db = SQLAlchemy()
application = Flask(__name__)
jwt = JWTManager(application)
celery = NewAcropolisCelery()


def create_app(**kwargs):
    from app.config import configs

    environment_state = kwargs.get('ENVIRONMENT', get_env())

    application.config.from_object(configs[environment_state])
    application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if kwargs.get('ENVIRONMENT'):
        application.config.update(kwargs)

    configure_logging()

    report_missing_config()

    db.init_app(application)

    if kwargs.get('is_celery'):
        celery.init_app(application)

    register_blueprint()

    init_app(application)

    return application


def init_app(app):
    app.jinja_loader = jinja2.FileSystemLoader([os.getcwd() + '/app/templates'])

    app.jinja_env.globals['API_BASE_URL'] = app.config['API_BASE_URL']
    app.jinja_env.globals['FRONTEND_URL'] = app.config['FRONTEND_URL']
    app.jinja_env.globals['IMAGES_URL'] = os.environ.get('IMAGES_URL', app.config['API_BASE_URL'] + '/images')

    @app.before_request
    def check_for_apikey():
        # print("check: ", request)
        pass


def register_blueprint():
    from app.rest import base_blueprint
    from app.routes.articles.rest import article_blueprint, articles_blueprint
    from app.routes.authentication.rest import auth_blueprint
    from app.routes.emails.rest import emails_blueprint
    from app.routes.events.rest import events_blueprint
    from app.routes.fees.rest import fees_blueprint, fee_blueprint
    from app.routes.event_dates.rest import event_dates_blueprint, event_date_blueprint
    from app.routes.event_types.rest import event_types_blueprint, event_type_blueprint
    from app.routes.legacy.rest import legacy_blueprint
    from app.routes.magazines.rest import magazines_blueprint
    from app.routes.marketings.rest import marketings_blueprint
    from app.routes.orders.rest import orders_blueprint
    from app.routes.members.rest import members_blueprint
    from app.routes.speakers.rest import speakers_blueprint, speaker_blueprint
    from app.routes.users.rest import users_blueprint, user_blueprint
    from app.routes.venues.rest import venues_blueprint, venue_blueprint
    application.register_blueprint(base_blueprint)
    application.register_blueprint(auth_blueprint)
    application.register_blueprint(article_blueprint)
    application.register_blueprint(articles_blueprint)
    application.register_blueprint(emails_blueprint)
    application.register_blueprint(events_blueprint)
    application.register_blueprint(event_date_blueprint)
    application.register_blueprint(event_dates_blueprint)
    application.register_blueprint(event_types_blueprint)
    application.register_blueprint(event_type_blueprint)
    application.register_blueprint(fees_blueprint)
    application.register_blueprint(fee_blueprint)
    application.register_blueprint(legacy_blueprint)
    application.register_blueprint(magazines_blueprint)
    application.register_blueprint(marketings_blueprint)
    application.register_blueprint(members_blueprint)
    application.register_blueprint(orders_blueprint)
    application.register_blueprint(speakers_blueprint)
    application.register_blueprint(speaker_blueprint)
    application.register_blueprint(users_blueprint)
    application.register_blueprint(user_blueprint)
    application.register_blueprint(venues_blueprint)
    application.register_blueprint(venue_blueprint)


def get_env():
    if 'www-preview' in get_root_path():
        return 'preview'
    elif 'www-live' in get_root_path():
        return 'live'
    else:
        return os.environ.get('ENVIRONMENT', 'development')


def get_root_path():
    return application.root_path


def report_missing_config():  # pragma: no cover
    if application.config.get('ENVIRONMENT') == 'test':
        return
    from app.config import Config
    for key in [k for k in Config.__dict__.keys() if k[:1] != '_']:
        if not application.config.get(key):
            application.logger.warning('Missing config setting: %s', key)


def configure_logging():
    if not application.config.get('APP_SERVER'):
        return

    ch = logging.StreamHandler()
    if ch in application.logger.handlers:
        return

    del application.logger.handlers[:]

    f = LogTruncatingFormatter(LOG_FORMAT.format(get_env()))
    ch.setFormatter(f)
    application.logger.addHandler(ch)

    rfh = RotatingFileHandler('logs/app.log', maxBytes=10000, backupCount=3)
    rfh.setLevel(logging.DEBUG)
    rfh.setFormatter(f)

    application.logger.addHandler(rfh)

    if application.config.get('APP_SERVER') == 'gunicorn':
        gunicorn_access_logger = logging.getLogger('gunicorn.access')
        application.logger.handlers.extend(gunicorn_access_logger.handlers)

        gunicorn_error_logger = logging.getLogger('gunicorn.error')
        application.logger.handlers.extend(gunicorn_error_logger.handlers)

        gunicorn_access_logger.addHandler(rfh)
        gunicorn_error_logger.addHandler(rfh)

        gunicorn_access_logger.addHandler(ch)
        gunicorn_error_logger.addHandler(ch)

        setup_gce_logging()

        application.logger.info('Gunicorn logging configured')
    else:
        werkzeug_log = logging.getLogger('werkzeug')
        werkzeug_log.setLevel(logging.DEBUG)

        werkzeug_log.addHandler(ch)
        werkzeug_log.addHandler(rfh)

        application.logger.info('Flask logging configured')

    db_name = application.config.get('SQLALCHEMY_DATABASE_URI').split('/')[-1]
    application.logger.debug("connected to db: {}".format(db_name))


def setup_gce_logging():  # pragma: no cover
    if (
        'ENABLE_GOOGLE_LOGGING' not in os.environ and
        application.config['SQLALCHEMY_DATABASE_URI'][:22] in ['postgresql://localhost', 'db://localhost/test_db']
    ):
        return

    import google.cloud.logging

    client = google.cloud.logging.Client()

    handler = client.get_default_handler()
    cloud_logger = logging.getLogger("cloudLogger")
    cloud_logger.setLevel(logging.INFO)
    cloud_logger.addHandler(handler)

    client.setup_logging(log_level=logging.INFO, excluded_loggers=("syslog",))


class LogTruncatingFormatter(logging.Formatter):
    def format(self, record):
        START_LOG = '127.0.0.1 - - ['
        if 'msg' in dir(record) and record.msg[:15] == START_LOG:
            record.msg = record.msg[42:]
        return super(LogTruncatingFormatter, self).format(record)
