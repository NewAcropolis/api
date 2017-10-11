from flask import (
    jsonify,
    current_app,
    json)
from jsonschema import ValidationError
from sqlalchemy.exc import SQLAlchemyError, DataError
from sqlalchemy.orm.exc import NoResultFound
from flask_jwt_extended.exceptions import (
    JWTDecodeError, NoAuthorizationError, InvalidHeaderError, WrongTokenError,
    RevokedTokenError, FreshTokenRequired, CSRFError, UserLoadError,
    UserClaimsVerificationError
)


def register_errors(blueprint):

    @blueprint.errorhandler(ValidationError)
    def validation_error(error):
        current_app.logger.exception(error)
        return jsonify(json.loads(error.message)), 400

    @blueprint.errorhandler(400)
    def bad_request(e):
        msg = e.description or "Invalid request parameters"
        current_app.logger.exception(msg)
        return jsonify(result='error', message=str(msg)), 400

    @blueprint.errorhandler(NoAuthorizationError)
    @blueprint.errorhandler(401)
    def unauthorized(e):
        error_message = "Unauthorized, authentication token must be provided"
        return jsonify(result='error', message=error_message), 401, [('WWW-Authenticate', 'Bearer')]

    @blueprint.errorhandler(403)
    def forbidden(e):
        error_message = "Forbidden, invalid authentication token provided"
        return jsonify(result='error', message=error_message), 403

    @blueprint.errorhandler(NoResultFound)
    @blueprint.errorhandler(DataError)
    def no_result_found(e):
        current_app.logger.exception(e)
        return jsonify(result='error', message="No result found"), 404

    @blueprint.errorhandler(SQLAlchemyError)
    def db_error(e):
        current_app.logger.exception(e)
        if hasattr(e, 'orig') and hasattr(e.orig, 'pgerror') and e.orig.pgerror and \
            ('duplicate key value violates unique constraint "services_name_key"' in e.orig.pgerror or
                'duplicate key value violates unique constraint "services_email_from_key"' in e.orig.pgerror):
            return jsonify(
                result='error',
                message={'name': ["Duplicate service name '{}'".format(
                    e.params.get('name', e.params.get('email_from', ''))
                )]}
            ), 400
        return jsonify(result='error', message="Internal server error"), 500

    # this must be defined after all other error handlers since it catches the generic Exception object
    @blueprint.app_errorhandler(500)
    @blueprint.errorhandler(Exception)
    def internal_server_error(e):
        current_app.logger.exception(e)
        return jsonify(result='error', message="Internal server error"), 500
