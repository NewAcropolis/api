from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
    url_for
)
from flask_jwt_extended import jwt_required

from app.dao import dao_create_record
from app.dao.magazines_dao import dao_get_magazine_by_id, dao_get_magazine_by_old_id, dao_get_magazines
from app.errors import register_errors, InvalidRequest
from app.models import Magazine
from app.routes.magazines import get_magazine_filename
from app.routes.magazines.schemas import post_create_magazine_schema, post_import_magazine_schema
from app.schema_validation import validate
from app.utils.storage import Storage

magazines_blueprint = Blueprint('magazines', __name__)
register_errors(magazines_blueprint)


@magazines_blueprint.route('/magazine/import', methods=['POST'])
@jwt_required
def import_magazine():
    data = request.get_json(force=True)

    validate(data, post_import_magazine_schema)

    magazine = Magazine(
        old_id=data['old_id'],
        title=data['title'],
        old_filename=data['old_filename'],
        filename=data['filename']
    )

    dao_create_record(magazine)

    return jsonify(magazine.serialize()), 201


@magazines_blueprint.route('/magazine', methods=['POST'])
@jwt_required
def create_magazine():
    data = request.get_json(force=True)

    validate(data, post_create_magazine_schema)

    new_filename = get_magazine_filename(data['filename'])

    if new_filename:
        magazine = Magazine(
            title=data['title'],
            filename=new_filename
        )

        storage = Storage(current_app.config['STORAGE'])

        storage.upload_blob_from_base64string(
            data['filename'],
            magazine.filename,
            data['pdf_data'],
            content_type='application/pdf'
        )

        dao_create_record(magazine)

        return jsonify(magazine.serialize()), 201

    raise InvalidRequest('Invalid filename for magazine: {}'.format(data['filename']), 400)


@magazines_blueprint.route('/magazines', methods=['GET'])
@jwt_required
def get_magazines():
    magazines = [m.serialize() if m else None for m in dao_get_magazines()]

    return jsonify(magazines)


@magazines_blueprint.route('/magazine/<uuid:id>', methods=['GET'])
@jwt_required
def get_magazine_by_id(id):
    magazine = dao_get_magazine_by_id(id)
    return jsonify(magazine.serialize())


@magazines_blueprint.route('/magazine/<int:old_id>', methods=['GET'])
@jwt_required
def get_magazine_by_old_id(old_id):
    magazine = dao_get_magazine_by_old_id(old_id)
    return jsonify(magazine.serialize())
