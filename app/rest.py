import threading
from queue import Queue
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from flask import Blueprint, jsonify, current_app
import os

from app import celery
from app import db
from app.errors import register_errors

base_blueprint = Blueprint('base', __name__)
register_errors(base_blueprint)


def are_celery_workers_running():
    def worker(q):
        i = celery.control.inspect()
        q.put(i.stats())

    q = Queue()
    threading.Thread(target=worker, args=(q,)).start()
    result = q.get()
    if result:
        return 'celery@worker-{}'.format(current_app.config.get('ENVIRONMENT')) in result


@base_blueprint.route('/')
def get_info():
    workers_running = False
    if 'http://localhost' not in current_app.config['API_BASE_URL'] and os.environ.get('DB_HOST') != 'db':
        workers_running = are_celery_workers_running()

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
        'commit': current_app.config['GITHUB_SHA'],
        'workers': 'Running' if workers_running else 'Not running'
    }

    if current_app.config.get('EMAIL_RESTRICT'):  # pragma: no cover
        resp['email_restrict'] = True
    return jsonify(resp)


@base_blueprint.route('/info')
def get_info_without_db():
    current_app.logger.info('get_info_without_db')

    resp = {
        'environment': current_app.config['ENVIRONMENT'],
        'commit': current_app.config['GITHUB_SHA'],
    }

    if current_app.config.get('EMAIL_RESTRICT'):  # pragma: no cover
        resp['email_restrict'] = True
    return jsonify(resp)
