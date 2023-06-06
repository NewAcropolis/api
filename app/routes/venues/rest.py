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

from app.dao.venues_dao import (
    dao_create_venue,
    dao_get_venues,
    dao_update_venue,
    dao_get_venue_by_id
)
from app.errors import register_errors

from app.routes.venues.schemas import (
    post_create_venue_schema,
    post_create_venues_schema,
    post_import_venues_schema,
    post_update_venue_schema
)
from app.models import Venue
from app.schema_validation import validate

venues_blueprint = Blueprint('venues', __name__)
venue_blueprint = Blueprint('venue', __name__)
register_errors(venues_blueprint)
register_errors(venue_blueprint)


@venues_blueprint.route('/venues')
@jwt_required()
def get_venues():
    venues = [e.serialize() if e else None for e in dao_get_venues()]
    return jsonify(venues)


@venue_blueprint.route('/venue/<uuid:venue_id>', methods=['GET'])
def get_venue_by_id(venue_id):
    current_app.logger.info('get_venue: {}'.format(venue_id))
    venue = dao_get_venue_by_id(venue_id)
    return jsonify(venue.serialize())


@venue_blueprint.route('/venue', methods=['POST'])
def create_venue():
    data = request.get_json(force=True)

    validate(data, post_create_venue_schema)

    venue = Venue(**data)

    dao_create_venue(venue)
    return jsonify(venue.serialize()), 201


@venues_blueprint.route('/venues', methods=['POST'])
@jwt_required()
def create_venues():
    data = request.get_json(force=True)

    validate(data, post_create_venues_schema)

    venues = []
    for item in data:
        venue = Venue.query.filter(Venue.name == item['name']).first()
        if not venue:
            venue = Venue(**item)
            venues.append(venue)
            dao_create_venue(venue)
        else:
            current_app.logger.info('venue already exists: {}'.format(venue.name))
    return jsonify([v.serialize() for v in venues]), 201


@venues_blueprint.route('/venues/import', methods=['POST'])
@jwt_required()
def import_venues():
    data = request.get_json(force=True)

    validate(data, post_import_venues_schema)

    venues = []
    for item in data:
        if not item["name"]:
            item["name"] = "Head branch"

        venue = Venue.query.filter(Venue.old_id == item['id']).first()
        if not venue:
            venue = Venue(
                old_id=item['id'],
                name=item['name'],
                address=item['address'],
                directions="<div>Bus: {bus}</div><div>Train: {train}</div>".format(bus=item['bus'], train=item['tube'])
            )
            venues.append(venue)
            dao_create_venue(venue)
        else:
            current_app.logger.info('venue already exists: {}'.format(venue.name))
    return jsonify([v.serialize() for v in venues]), 201


@venue_blueprint.route('/venue/<uuid:venue_id>', methods=['POST'])
def update_venue(venue_id):
    data = request.get_json(force=True)

    validate(data, post_update_venue_schema)

    fetched_venue = dao_get_venue_by_id(venue_id)

    dao_update_venue(venue_id, **data)

    return jsonify(fetched_venue.serialize()), 200
