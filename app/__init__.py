import os
import logging
import sys
from logging.handlers import RotatingFileHandler

import jinja2
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
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

    register_blueprints()

    init_app(application)

    return application


def init_app(app):
    app.jinja_loader = jinja2.FileSystemLoader([os.getcwd() + '/app/templates'])

    app.jinja_env.globals['API_BASE_URL'] = app.config['PREVIEW_API_BASE_URL'] \
        if app.config.get('EMAIL_TEST') else app.config['API_BASE_URL']
    app.jinja_env.globals['FRONTEND_URL'] = app.config['FRONTEND_URL']
    app.jinja_env.globals['IMAGES_URL'] = f"{app.config['PREVIEW_API_BASE_URL']}/static/images" \
        if app.config.get('EMAIL_TEST') else app.config['IMAGES_URL']

    @app.before_request
    def check_for_apikey():
        # print("check: ", request)
        pass


def register_blueprint(bp):
    if bp.name not in application.blueprints.keys():
        application.register_blueprint(bp)


def register_blueprints():
    from app.rest import base_blueprint
    from app.routes.articles.rest import article_blueprint, articles_blueprint
    from app.routes.authentication.rest import auth_blueprint
    from app.routes.books.rest import book_blueprint, books_blueprint
    from app.routes.emails.rest import emails_blueprint
    from app.routes.email_providers.rest import email_providers_blueprint
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
    from app.routes.stats.rest import stats_blueprint
    from app.routes.users.rest import users_blueprint, user_blueprint
    from app.routes.venues.rest import venues_blueprint, venue_blueprint
    register_blueprint(base_blueprint)
    register_blueprint(auth_blueprint)
    register_blueprint(article_blueprint)
    register_blueprint(articles_blueprint)
    register_blueprint(book_blueprint)
    register_blueprint(books_blueprint)
    register_blueprint(emails_blueprint)
    register_blueprint(email_providers_blueprint)
    register_blueprint(events_blueprint)
    register_blueprint(event_date_blueprint)
    register_blueprint(event_dates_blueprint)
    register_blueprint(event_types_blueprint)
    register_blueprint(event_type_blueprint)
    register_blueprint(fees_blueprint)
    register_blueprint(fee_blueprint)
    register_blueprint(legacy_blueprint)
    register_blueprint(magazines_blueprint)
    register_blueprint(marketings_blueprint)
    register_blueprint(members_blueprint)
    register_blueprint(orders_blueprint)
    register_blueprint(speakers_blueprint)
    register_blueprint(speaker_blueprint)
    register_blueprint(stats_blueprint)
    register_blueprint(users_blueprint)
    register_blueprint(user_blueprint)
    register_blueprint(venues_blueprint)
    register_blueprint(venue_blueprint)


def get_env():
    if 'www-preview' in get_root_path():
        return 'preview'
    elif 'www-live' in get_root_path():
        return 'live'
    else:
        env = os.environ.get('ENVIRONMENT', 'development')
        return 'development' if env == 'dev' else env


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

    # set max log file size to 10mb and 3 file backups
    rfh = RotatingFileHandler('logs/app.log', maxBytes=10240000, backupCount=3)
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

        application.logger.info('Gunicorn logging configured')
    else:
        werkzeug_log = logging.getLogger('werkzeug')
        werkzeug_log.setLevel(logging.DEBUG)

        werkzeug_log.addHandler(ch)
        werkzeug_log.addHandler(rfh)

        application.logger.info('Flask logging configured')

    db_name = application.config.get('SQLALCHEMY_DATABASE_URI').split('/')[-1]
    application.logger.debug("connected to db: {}".format(db_name))


class LogTruncatingFormatter(logging.Formatter):
    def format(self, record):
        START_LOG = '127.0.0.1 - - ['
        if 'msg' in dir(record) and str(record.msg)[:15] == START_LOG:
            offset = 37 if record.msg[37:].startswith("\"%s\"") else 42
            record.msg = record.msg[offset:]
        return super().format(record)
