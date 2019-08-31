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
    return jsonify(
        environment=current_app.config['ENVIRONMENT'],
        info=full_name,
        commit=current_app.config['TRAVIS_COMMIT']
    )
