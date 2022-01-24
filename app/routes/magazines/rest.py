import base64
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
    send_file
)
from flask_jwt_extended import jwt_required
from io import StringIO, BytesIO
import requests

from app.na_celery import upload_tasks
from app.comms.stats import send_ga_event
from app.dao import dao_create_record, dao_update_record
from app.dao.emails_dao import dao_create_email
from app.dao.magazines_dao import (
    dao_get_magazine_by_id, dao_get_magazine_by_old_id, dao_get_magazines, dao_get_latest_magazine
)
from app.dao.users_dao import dao_get_users
from app.errors import register_errors, InvalidRequest
from app.models import Email, Magazine, MAGAZINE, READY
from app.routes.magazines import get_magazine_filename
from app.routes.magazines.schemas import (
    post_create_magazine_schema, post_import_magazine_schema, post_update_magazine_schema
)
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

        dao_create_record(magazine)

        upload_tasks.upload_magazine.apply_async((str(magazine.id), data['pdf_data']))

        return jsonify(magazine.serialize()), 201

    raise InvalidRequest('Invalid filename for magazine: {}'.format(data['filename']), 400)


@magazines_blueprint.route('/magazine/<uuid:id>', methods=['POST'])
@jwt_required
def update_magazine(id):
    data = request.get_json(force=True)

    validate(data, post_update_magazine_schema)

    new_filename = get_magazine_filename(data['filename'])
    if new_filename:
        magazine = Magazine(
            id=id,
            title=data['title'],
            filename=new_filename,
            topics=data['topics'],
            tags=data['tags']
        )

        if 'pdf_data' in data:
            upload_tasks.upload_magazine.apply_async((id, data['pdf_data']))

        dao_update_record(
            Magazine,
            id=id,
            title=magazine.title,
            filename=magazine.filename,
            topics=magazine.topics,
            tags=magazine.tags
        )

        return jsonify(magazine.serialize()), 200

    raise InvalidRequest('Invalid filename for magazine: {}'.format(data['filename']), 400)


@magazines_blueprint.route('/magazine/latest', methods=['GET'])
@jwt_required
def get_latest_magazine():
    magazine = dao_get_latest_magazine()

    return jsonify(magazine.serialize())


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


@magazines_blueprint.route('/magazine/download_pdf/<uuid:magazine_id>', methods=['GET'])
def download_pdf(magazine_id, category="magazine_download"):
    magazine = dao_get_magazine_by_id(magazine_id)

    send_ga_event("magazine download", category, "download", magazine.title)

    pdf_filename = 'pdfs/{}'.format(magazine.filename)
    storage = Storage(current_app.config['STORAGE'])

    pdf = BytesIO(storage.get_blob(pdf_filename))
    return send_file(pdf, as_attachment=True, attachment_filename=magazine.filename, mimetype='application/pdf')
