import datetime
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    get_jwt,
    jwt_required,
)
from app import jwt
from app.routes.authentication.errors import AuthenticationError
from app.routes.authentication.schemas import post_login_schema
from app.dao.blacklist_dao import store_token, prune_database, is_token_revoked
from app.errors import register_errors
from app.schema_validation import validate

blacklist = set()
auth_blueprint = Blueprint('auth', __name__, url_prefix='/auth')
register_errors(auth_blueprint)


@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, decrypted_token):
    jti = decrypted_token['jti']
    current_app.logger.info('check_token: {}, {}'.format(jti, blacklist))
    return is_token_revoked(decrypted_token)


@auth_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    validate(data, post_login_schema)

    username = data['username']
    password = data['password']

    if username != current_app.config['ADMIN_CLIENT_ID'] or password != current_app.config['ADMIN_CLIENT_SECRET']:
        raise AuthenticationError(username=username, password=password)

    expiry = datetime.timedelta(minutes=current_app.config['TOKEN_EXPIRY'])

    # Identity can be any data that is json serializable
    access_token = create_access_token(identity=username, expires_delta=expiry)
    refresh_token = create_refresh_token(identity=username)

    resp = jsonify(
        {
            'login': True,
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    )
    return resp, 200


@auth_blueprint.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    username = get_jwt_identity()
    if username != current_app.config['ADMIN_CLIENT_ID']:
        raise AuthenticationError(message='Bad username')

    resp = {
        'access_token': create_access_token(identity=username)
    }
    return jsonify(resp), 200


@auth_blueprint.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    prune_database()
    store_token(get_jwt())
    return jsonify({"logout": True}), 200


# Endpoint for revoking the current users refresh token
@auth_blueprint.route('/logout-refresh', methods=['DELETE'])
@jwt_required(refresh=True)
def logout_refresh():
    prune_database()
    store_token(get_jwt())
    return jsonify({"logout": True}), 200
