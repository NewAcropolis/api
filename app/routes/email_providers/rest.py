import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request
)

from app.errors import register_errors
from app.models import EmailProvider

from flask_jwt_extended import jwt_required
from app.dao.email_providers_dao import (
    dao_create_email_provider, dao_update_email_provider,
    dao_get_email_provider_by_id, dao_get_first_email_provider,
    dao_get_email_providers
)
from app.routes.email_providers.schemas import post_create_email_provider_schema, post_update_email_provider_schema
from app.schema_validation import validate

email_providers_blueprint = Blueprint('email_provider', __name__)
register_errors(email_providers_blueprint)


@email_providers_blueprint.route('/email_provider', methods=['POST'])
@jwt_required()
def create_email_provider():
    data = request.get_json(force=True)

    validate(data, post_create_email_provider_schema)

    email_provider = EmailProvider(**data)

    dao_create_email_provider(email_provider)

    return jsonify(email_provider.serialize()), 201


@email_providers_blueprint.route('/email_provider/<uuid:email_provider_id>', methods=['POST'])
@jwt_required()
def update_email_provider(email_provider_id):
    data = request.get_json(force=True)

    validate(data, post_update_email_provider_schema)

    fetched_email_provider = dao_get_email_provider_by_id(email_provider_id)

    dao_update_email_provider(email_provider_id, **data)

    return jsonify(fetched_email_provider.serialize()), 200


@email_providers_blueprint.route('/email_providers', methods=['GET'])
@jwt_required()
def get_email_providers():
    email_providers = []
    for fetched_email_provider in dao_get_email_providers():
        email_provider_json = fetched_email_provider.serialize()
        if email_provider_json['api_key']:
            shortened_api_key = email_provider_json['api_key'][-10:]
            del email_provider_json['api_key']
            email_provider_json['shortened_api_key'] = shortened_api_key

        if email_provider_json['smtp_password']:
            shortened_smtp_pass = email_provider_json['smtp_password'][-5:]
            del email_provider_json['smtp_password']
            email_provider_json['shortened_smtp_password'] = shortened_smtp_pass
        email_providers.append(email_provider_json)
    return jsonify(email_providers), 200
