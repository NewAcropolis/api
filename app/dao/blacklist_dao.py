from datetime import datetime

from sqlalchemy.orm.exc import NoResultFound
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask_jwt_extended import decode_token, get_jwt_identity

from app import db
from app.dao.decorators import transactional
from app.routes.authentication.errors import TokenNotFound
from app.models import TokenBlacklist


@transactional
def store_token(decoded_token):
    jti = decoded_token['jti']
    token_type = decoded_token['type']
    user_identity = decoded_token['identity']
    expires = datetime.fromtimestamp(decoded_token['exp'])

    db_token = TokenBlacklist(
        jti=jti,
        token_type=token_type,
        user_identity=user_identity,
        expires=expires,
        revoked=True,
    )

    db.session.add(db_token)


def is_token_revoked(decoded_token):
    jti = decoded_token['jti']
    try:
        token = TokenBlacklist.query.filter_by(jti=jti).one()
        return token.revoked
    except NoResultFound:
        return False


def get_user_tokens(user_identity):
    return TokenBlacklist.query.filter_by(user_identity=user_identity).all()


@transactional
def unrevoke_token(token_id, user):
    try:
        token = TokenBlacklist.query.filter_by(id=token_id, user_identity=user).one()
        db.session.delete(token)
    except NoResultFound:
        raise TokenNotFound("Could not find the token {}".format(token_id))


@transactional
def prune_database():
    now = datetime.now()
    expired = TokenBlacklist.query.filter(TokenBlacklist.expires < now).all()
    for token in expired:
        db.session.delete(token)
