import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from app.dao.users_dao import (
    dao_get_users,
    dao_get_user_by_email,
    dao_get_user_by_id,
    dao_create_user,
    dao_update_user
)
from app.errors import register_errors, InvalidRequest
from app.models import User, ACCESS_AREAS, USER_ADMIN
from app.schema_validation import validate
from app.routes.users.schemas import (
    post_create_user_schema,
    post_update_user_schema
)

users_blueprint = Blueprint('users', __name__)
user_blueprint = Blueprint('user', __name__)

register_errors(users_blueprint)
register_errors(user_blueprint)


@users_blueprint.route('/users')
@jwt_required()
def get_users():
    users = [s.serialize() if s else None for s in dao_get_users()]
    return jsonify(users)


@user_blueprint.route('/user/<email>', methods=['GET'])
@jwt_required()
def get_user_by_email(email):
    user = dao_get_user_by_email(email)
    if user:
        return jsonify(user.serialize())
    raise InvalidRequest("{} not found".format(email), 404)


@user_blueprint.route('/user/<email>/is_admin', methods=['GET'])
@jwt_required()
def is_admin(email):
    return jsonify({
        'email': email,
        'is_admin': email in current_app.config['ADMIN_USERS'] or
        email in [u.email for u in dao_get_users() if u.is_admin()]
    })


@user_blueprint.route('/user', methods=['POST'])
@jwt_required()
def create_user():
    data = request.get_json(force=True)

    validate(data, post_create_user_schema)

    current_app.logger.info('Creating user {}'.format(data['email']))

    if data['email'].split('@')[1] != current_app.config['EMAIL_DOMAIN']:
        raise InvalidRequest("{} not in correct domain".format(data['email']), 400)

    if data['email'] in current_app.config['ADMIN_USERS']:
        data['access_area'] = USER_ADMIN
    elif data.get('access_area'):
        for area in data['access_area'].split(','):
            if area and area not in ACCESS_AREAS:
                raise InvalidRequest("{} not supported access area".format(area), 400)

    data['active'] = True

    user = User(**data)

    dao_create_user(user)

    current_app.logger.info('Created user {}'.format(user.email))

    return jsonify(user.serialize()), 201


@user_blueprint.route('/user/<uuid:user_id>', methods=['POST'])
@jwt_required()
def update_user(user_id):
    data = request.get_json(force=True)

    validate(data, post_update_user_schema)

    dao_update_user(user_id, **data)

    user = dao_get_user_by_id(user_id)

    return jsonify(user.serialize()), 200


@user_blueprint.errorhandler(IntegrityError)
def handle_integrity_error(exc):
    """
    Handle integrity errors caused by the unique constraint on users_email_key
    """
    if 'users_email_key' in str(exc):
        return jsonify(result="error",
                       message="User email already exists"), 400

    current_app.logger.exception(exc)
    return jsonify(result='error', message="Internal server error"), 500
