from flask import Blueprint, jsonify, current_app

from app import db
from app.errors import register_errors

base_blueprint = Blueprint('', __name__)
register_errors(base_blueprint)


@base_blueprint.route('/')
def get_info():
    current_app.logger.info('get_info')
    query = 'SELECT version_num FROM alembic_version'
    try:
        full_name = db.session.execute(query).fetchone()[0]
    except Exception as e:
        current_app.logger.error('Database exception: %r', e)
        full_name = 'Database error, check logs'

    resp = {
        'environment': current_app.config['ENVIRONMENT'],
        'info': full_name,
        'commit': current_app.config['TRAVIS_COMMIT'],
    }

    if current_app.config.get('EMAIL_RESTRICT'):  # pragma: no cover
        resp['email_restrict'] = True
    return jsonify(resp)


@base_blueprint.route('/info')
def get_info_without_db():
    current_app.logger.info('get_info_without_db')

    resp = {
        'environment': current_app.config['ENVIRONMENT'],
        'commit': current_app.config['TRAVIS_COMMIT'],
    }

    if current_app.config.get('EMAIL_RESTRICT'):  # pragma: no cover
        resp['email_restrict'] = True
    return jsonify(resp)
