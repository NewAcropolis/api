import os
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)
from flask_jwt_extended import jwt_required

from app import logging
from app.dao.fees_dao import dao_create_fee, dao_get_fees, dao_update_fee, dao_get_fee_by_id
from app.errors import register_errors

from app.fees.schemas import post_create_fee_schema, post_update_fee_schema
from app.models import Fee
from app.schema_validation import validate

fees_blueprint = Blueprint('fees', __name__, url_prefix='/fees')
fee_blueprint = Blueprint('fee', __name__, url_prefix='/fee')
register_errors(fees_blueprint)
register_errors(fee_blueprint)


@fees_blueprint.route('')
@jwt_required
def get_fees():
    current_app.logger.info('get_fees')
    fees = [f.serialize() if f else None for f in dao_get_fees()]
    return jsonify(data=fees)


@fee_blueprint.route('/<uuid:fee_id>', methods=['GET'])
def get_fee_by_id(fee_id):
    current_app.logger.info('get_fee: {}'.format(fee_id))
    fee = dao_get_fee_by_id(fee_id)
    return jsonify(data=fee.serialize())


@fee_blueprint.route('', methods=['POST'])
def create_fee():
    data = request.get_json()

    validate(data, post_create_fee_schema)

    fee = Fee(**data)

    dao_create_fee(fee)
    return jsonify(data=fee.serialize()), 201


@fee_blueprint.route('/<uuid:fee_id>', methods=['POST'])
def update_fee(fee_id):
    data = request.get_json()

    validate(data, post_update_fee_schema)

    fetched_fee = dao_get_fee_by_id(fee_id)

    dao_update_fee(fetched_fee, **data)

    return jsonify(data=fetched_fee.serialize()), 200
