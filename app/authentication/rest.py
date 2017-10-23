import datetime
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    get_raw_jwt,
    jwt_refresh_token_required,
    jwt_required,
)
from app import jwt
from app.authentication.errors import AuthenticationError
from app.authentication.schemas import post_login_schema
from app.errors import register_errors
from app.schema_validation import validate

blacklist = set()
auth_blueprint = Blueprint('auth', __name__, url_prefix='/auth')
register_errors(auth_blueprint)


def add_blacklist(jti):
    blacklist.add(jti)


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return jti in blacklist


@auth_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    validate(data, post_login_schema)

    username = data['username']
    password = data['password']

    if username != current_app.config['ADMIN_CLIENT_ID'] or password != current_app.config['ADMIN_PASSWORD']:
        raise AuthenticationError()
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
@jwt_refresh_token_required
def refresh():
    current_user = get_jwt_identity()
    ret = {
        'access_token': create_access_token(identity=current_user)
    }
    return jsonify(ret), 200


@auth_blueprint.route('/logout', methods=['POST'])
@jwt_required
def logout():
    jti = get_raw_jwt()['jti']
    add_blacklist(jti)
    return jsonify({"logout": True}), 200
