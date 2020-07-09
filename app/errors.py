from flask import (
    jsonify,
    current_app,
    json)
from jsonschema import ValidationError
from jwt.exceptions import DecodeError, ExpiredSignatureError
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask_jwt_extended.exceptions import (
    JWTDecodeError,
    NoAuthorizationError,
    InvalidHeaderError,
    WrongTokenError,
    RevokedTokenError,
    FreshTokenRequired,
    CSRFError,
    UserLoadError,
    UserClaimsVerificationError
)

from app.routes.authentication.errors import AuthenticationError, TokenNotFound


class InvalidRequest(Exception):
    code = None
    fields = []

    def __init__(self, message, status_code):
        super()
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return {'result': 'error', 'message': self.message}


class PaypalException(Exception):
    pass


def register_errors(blueprint):

    @blueprint.errorhandler(ValidationError)
    def validation_error(error):
        current_app.logger.exception(error)
        return jsonify(json.loads(error.message)), 400

    @blueprint.errorhandler(InvalidRequest)
    def invalid_data(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        current_app.logger.info('Invalid data: {}'.format(error.message))
        return response

    @blueprint.errorhandler(400)
    def bad_request(e):
        msg = e.description or "Invalid request parameters"
        current_app.logger.exception(msg)
        return jsonify(result='error', message=str(msg)), 400

    @blueprint.errorhandler(TokenNotFound)
    def token_not_found(e):
        msg = 'Token not found'
        current_app.logger.exception('TokenNotFound: {}'.format(e))
        return jsonify(result='error', message=msg), 400

    @blueprint.errorhandler(RevokedTokenError)
    def token_revoked(e):
        current_app.logger.exception(e)
        return jsonify(result='error', message=str(e)), 400

    @blueprint.errorhandler(DecodeError)
    def decode_error(e):
        msg = 'Decode error on auth token'
        current_app.logger.exception(e)
        return jsonify(result='error', message=str(msg)), 400

    @blueprint.errorhandler(InvalidHeaderError)
    def invalid_header(e):
        msg = 'Invalid header error'
        current_app.logger.exception(msg)
        return jsonify(result='error', message=str(msg)), 400

    @blueprint.errorhandler(IntegrityError)
    def integrity_error(exc):
        if 'events_event_state_fkey' in str(exc):
            return jsonify(result="error",
                           message="Event state: '{}' not valid".format(exc.params['event_state'])), 400
        elif 'duplicate key value violates unique constraint' in str(exc):
            return jsonify(result="error",
                           message="Duplicate key: {}".format(exc.orig)), 400

        current_app.logger.exception(exc)
        return jsonify(result='error', message="Internal server error"), 500

    @blueprint.errorhandler(ExpiredSignatureError)
    def expire_signature_error(e):
        msg = 'Signature expired'
        current_app.logger.exception(msg)
        return jsonify(result='error', message=str(msg)), 401

    @blueprint.errorhandler(NoAuthorizationError)
    @blueprint.errorhandler(401)
    def unauthorized(e):
        current_app.logger.exception(e)
        error_message = "Unauthorized, authentication token must be provided"
        return jsonify(result='error', message=error_message), 401, [('WWW-Authenticate', 'Bearer')]

    @blueprint.errorhandler(AuthenticationError)
    def authentication_error(e):
        current_app.logger.exception(e)
        error_message = "{}, {}, {}".format(e.error_message, e.username, e.password)
        return jsonify(result='error', message=error_message), 403

    @blueprint.errorhandler(403)
    def forbidden(e):
        current_app.logger.exception(e)
        error_message = "Forbidden, invalid authentication token provided"
        return jsonify(result='error', message=error_message), 403

    @blueprint.errorhandler(NoResultFound)
    @blueprint.errorhandler(DataError)
    def no_result_found(e):
        current_app.logger.exception(e)
        return jsonify(result='error', message="No result found"), 404

    # this must be defined after all other error handlers since it catches the generic Exception object
    @blueprint.app_errorhandler(500)
    @blueprint.errorhandler(Exception)
    def internal_server_error(e):
        current_app.logger.exception(e)
        return jsonify(result='error', message="Internal server error: {}".format(str(e))), 500
