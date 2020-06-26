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
    dao_create_email_provider, dao_update_email_provider, dao_get_email_provider_by_id
)
from app.routes.email_providers.schemas import post_create_email_provider_schema, post_update_email_provider_schema
from app.schema_validation import validate

email_providers_blueprint = Blueprint('email_provider', __name__)
register_errors(email_providers_blueprint)


@email_providers_blueprint.route('/email_provider', methods=['POST'])
@jwt_required
def create_email_provider():
    data = request.get_json(force=True)

    validate(data, post_create_email_provider_schema)

    email_provider = EmailProvider(**data)

    dao_create_email_provider(email_provider)

    return jsonify(email_provider.serialize()), 201


@email_providers_blueprint.route('/email_provider/<uuid:email_provider_id>', methods=['POST'])
@jwt_required
def update_email_provider(email_provider_id):
    data = request.get_json(force=True)

    validate(data, post_update_email_provider_schema)

    fetched_email_provider = dao_get_email_provider_by_id(email_provider_id)

    dao_update_email_provider(email_provider_id, **data)

    return jsonify(fetched_email_provider.serialize()), 200
