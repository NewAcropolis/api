import os

from flask import Blueprint
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import logging

logging.basicConfig(filename='logs/app.log', level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())

db = SQLAlchemy()
application = Flask(__name__)


def create_app(**kwargs):
    from app.config import configs

    environment_state = get_env()

    application.config.from_object(configs[environment_state])
    application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    application.config.update(kwargs)

    logging.debug("connected to db: {}".format(application.config['SQLALCHEMY_DATABASE_URI']))

    db.init_app(application)

    register_blueprint(application)

    return application


def register_blueprint(application):
    from app.events.rest import events_blueprint
    application.register_blueprint(events_blueprint, url_prefix='/events')


def get_env():
    if 'www-preview' in get_root_path():
        return 'preview'
    elif 'www-live' in get_root_path():
        return 'live'
    else:
        return os.environ.get('ENVIRONMENT_STATE', 'development')


def get_root_path():
    return application.root_path
