import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask import current_app
from functools import wraps

from app import db


def transactional(func):
    @wraps(func)
    def commit_or_rollback(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            db.session.commit()
            return res
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            raise
    return commit_or_rollback
