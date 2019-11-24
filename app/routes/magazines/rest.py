from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
    url_for
)
from flask_jwt_extended import jwt_required

from app.dao import dao_create_record
from app.dao.magazines_dao import dao_get_magazines
from app.errors import register_errors
from app.models import Magazine
from app.routes.magazines.schemas import post_import_magazine_schema
from app.schema_validation import validate

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


@magazines_blueprint.route('/magazines', methods=['GET'])
@jwt_required
def get_magazines(year=None):
    magazines = [m.serialize() if m else None for m in dao_get_magazines()]

    return jsonify(magazines)
