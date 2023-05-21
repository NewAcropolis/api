import pytest

from flask import json, url_for, Blueprint, Flask, jsonify, abort
from flask_jwt_extended.exceptions import (
    JWTDecodeError,
    NoAuthorizationError,
    InvalidHeaderError,
    WrongTokenError,
    RevokedTokenError,
    FreshTokenRequired,
    CSRFError,
    UserLookupError,
    UserClaimsVerificationError
)
from jsonschema import ValidationError
from jwt.exceptions import DecodeError, ExpiredSignatureError
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from app.routes.authentication.errors import AuthenticationError, TokenNotFound
from app.errors import register_errors, InvalidRequest, PaypalException


class WhenAnErrorOccurs(object):

    @pytest.fixture
    def error_app(self):
        app = Flask(__name__)
        app.config['TESTING'] = True

        error_blueprint = Blueprint('test_errors', __name__)
        register_errors(error_blueprint)

        @error_blueprint.route('/validation-error')
        def validation():
            raise ValidationError(json.dumps({"message": "Validation error"}))

        @error_blueprint.route('/status-400')
        def status_400():
            abort(400)

        @error_blueprint.route('/token-not-found')
        def token_not_found():
            raise TokenNotFound("Token not found")

        @error_blueprint.route('/revoked-token')
        def revoked_token():
            raise RevokedTokenError("Revoked token error")

        @error_blueprint.route('/decode-error')
        def decode_error():
            raise DecodeError()

        @error_blueprint.route('/invalid-header')
        def invalid_header():
            raise InvalidHeaderError()

        @error_blueprint.route('/expired-signature-error')
        def expire_signature_error():
            raise ExpiredSignatureError()

        @error_blueprint.route('/no-authorization-error')
        def no_authorization_error():
            raise NoAuthorizationError()

        @error_blueprint.route('/status-401')
        def status_401():
            abort(401)

        @error_blueprint.route('/authentication-error')
        def authentication_error():
            raise AuthenticationError(username='test_user', password='test_pass')

        @error_blueprint.route('/status-403')
        def status_403():
            abort(403)

        @error_blueprint.route('/no-result-found')
        def no_result_found():
            raise NoResultFound()

        @error_blueprint.route('/integrity-error')
        def integrity_error():
            raise IntegrityError("", "", "", "")

        @error_blueprint.route('/data-error')
        def data_error():
            raise DataError(None, None, None)

        @error_blueprint.route('/invalid-request')
        def invalid_request():
            raise InvalidRequest('Invalid request', 400)

        @error_blueprint.route('/paypal-err')
        def paypal_err():
            raise PaypalException('Paypal exception')

        @error_blueprint.route('/status-500')
        def status_500():
            abort(500)

        @error_blueprint.route('/exception')
        def exception():
            raise Exception()

        app.register_blueprint(error_blueprint)

        with app.test_request_context(), app.test_client() as client:
            yield client

    def it_handles_validation_error(self, error_app):
        response = error_app.get(
            path='/validation-error'
        )
        assert response.status_code == 400
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "Validation error"

    def it_handles_status_400(self, error_app):
        response = error_app.get(
            path='/status-400'
        )
        assert response.status_code == 400
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "The browser (or proxy) sent a request that this server could not understand."

    def it_handles_token_not_found(self, error_app):
        response = error_app.get(
            path='/token-not-found'
        )
        assert response.status_code == 400
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "Token not found"

    def it_handles_revoked_token(self, error_app):
        response = error_app.get(
            path='/revoked-token'
        )
        assert response.status_code == 400
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "Revoked token error"

    def it_handles_decode_error(self, error_app):
        response = error_app.get(
            path='/decode-error'
        )
        assert response.status_code == 400
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "Decode error on auth token"

    def it_handles_invalid_header(self, error_app):
        response = error_app.get(
            path='/invalid-header'
        )
        assert response.status_code == 400
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "Invalid header error"

    def it_handles_expired_signature_error(self, error_app):
        response = error_app.get(
            path='/expired-signature-error'
        )
        assert response.status_code == 401
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "Signature expired"

    def it_handles_no_authorization_error(self, error_app):
        response = error_app.get(
            path='/no-authorization-error'
        )
        assert response.status_code == 401
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "Unauthorized, authentication token must be provided"

    def it_handles_status_401(self, error_app):
        response = error_app.get(
            path='/status-401'
        )
        assert response.status_code == 401
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "Unauthorized, authentication token must be provided"

    def it_handles_no_authentication_error(self, error_app):
        response = error_app.get(
            path='/authentication-error'
        )
        assert response.status_code == 403
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "Bad username or password, test_user, test_pass"

    def it_handles_status_403(self, error_app):
        response = error_app.get(
            path='/status-403'
        )
        assert response.status_code == 403
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "Forbidden, invalid authentication token provided"

    def it_handles_result_not_found(self, error_app):
        response = error_app.get(
            path='/no-result-found'
        )
        assert response.status_code == 404
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "No result found"

    def it_handles_integrity_error(self, error_app):
        response = error_app.get(
            path='/integrity-error'
        )
        assert response.status_code == 500
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "Internal server error"

    def it_handles_data_error(self, error_app):
        response = error_app.get(
            path='/data-error'
        )
        assert response.status_code == 404
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "No result found"

    def it_handles_invalid_request(self, error_app):
        response = error_app.get(
            path='/invalid-request'
        )
        assert response.status_code == 400
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "Invalid request"

    def it_handles_status_500(self, error_app):
        response = error_app.get(
            path='/status-500'
        )
        assert response.status_code == 500
        json_resp = json.loads(response.get_data(as_text=True))
        assert "Internal server error: 500" in json_resp['message']

    def it_handles_paypal_exceptions(self, error_app):
        response = error_app.get(
            path='/paypal-err'
        )
        assert response.status_code == 500
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "Internal server error: Paypal exception"

    def it_handles_exeption(self, error_app):
        response = error_app.get(
            path='/exception'
        )
        assert response.status_code == 500
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "Internal server error: "
