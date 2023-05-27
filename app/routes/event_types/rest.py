import os
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)

from flask_jwt_extended import jwt_required

from app.dao.event_types_dao import (
    dao_create_event_type,
    dao_get_event_types,
    dao_update_event_type,
    dao_get_event_type_by_id
)
from app.errors import register_errors

from app.routes.event_types.schemas import (
    post_create_event_type_schema,
    post_import_event_types_schema,
    post_update_event_type_schema
)
from app.models import EventType
from app.schema_validation import validate

event_types_blueprint = Blueprint('event_types', __name__)
event_type_blueprint = Blueprint('event_type', __name__)
register_errors(event_types_blueprint)
register_errors(event_type_blueprint)


@event_types_blueprint.route('/event_types')
@jwt_required()
def get_event_types():
    current_app.logger.info('get_event_types')
    event_types = [e.serialize() if e else None for e in dao_get_event_types()]
    return jsonify(event_types)


@event_type_blueprint.route('/event_type/<uuid:event_type_id>', methods=['GET'])
def get_event_type_by_id(event_type_id):
    current_app.logger.info('get_event_type: {}'.format(event_type_id))
    event_type = dao_get_event_type_by_id(event_type_id)
    return jsonify(event_type.serialize())


@event_type_blueprint.route('/event_type', methods=['POST'])
@jwt_required()
def create_event_type():
    data = request.get_json()

    validate(data, post_create_event_type_schema)

    event_type = EventType(**data)

    dao_create_event_type(event_type)
    return jsonify(event_type.serialize()), 201


@event_types_blueprint.route('/event_types/import', methods=['POST'])
@jwt_required()
def import_event_types():
    data = request.get_json(force=True)

    validate(data, post_import_event_types_schema)

    event_types = []
    for item in data:
        event_type = EventType.query.filter(EventType.old_id == item['id']).first()
        if not event_type:
            event_type = EventType(
                old_id=item['id'],
                event_type=item['EventType'],
                event_desc=item['EventDesc'],
                event_filename=item['EventFilename'],
            )

            event_types.append(event_type)
            dao_create_event_type(event_type)
        else:
            current_app.logger.info('event type already exists: {}'.format(event_type.event_type))
    return jsonify([e.serialize() for e in event_types]), 201


@event_type_blueprint.route('/event_type/<uuid:event_type_id>', methods=['POST'])
@jwt_required()
def update_event_type(event_type_id):
    data = request.get_json()

    validate(data, post_update_event_type_schema)

    fetched_event_type = dao_get_event_type_by_id(event_type_id)

    dao_update_event_type(event_type_id, **data)

    return jsonify(fetched_event_type.serialize()), 200
