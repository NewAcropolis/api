import base64
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)
from flask_jwt_extended import jwt_required

from app.comms.email import get_email_html, send_email
from app.dao import dao_create_record, dao_update_record
from app.dao.emails_dao import dao_create_email
from app.dao.magazines_dao import dao_get_magazine_by_id, dao_get_magazine_by_old_id, dao_get_magazines
from app.dao.users_dao import dao_get_users
from app.errors import register_errors, InvalidRequest
from app.models import Email, Magazine, MAGAZINE, READY
from app.routes.magazines import get_magazine_filename
from app.routes.magazines.schemas import (
    post_create_magazine_schema, post_import_magazine_schema, post_update_magazine_schema
)
from app.schema_validation import validate
from app.utils.pdf import extract_topics
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

        topics = extract_topics(base64.b64decode(data['pdf_data']))
        if topics:
            magazine.topics = topics

        dao_create_record(magazine)

        email = Email(
            magazine_id=magazine.id,
            email_state=READY,
            email_type=MAGAZINE
        )
        dao_create_email(email)

        emails_to = [user.email for user in dao_get_users()]

        subject = 'Please review {}'.format(data['title'])

        # send email to admin users and ask them to log in in order to approve the email
        review_part = '<div>Please review this email: {}/emails/{}</div>'.format(
            current_app.config['FRONTEND_ADMIN_URL'], str(email.id))
        magazine_html = get_email_html(MAGAZINE, magazine_id=magazine.id)
        response = send_email(emails_to, subject, review_part + magazine_html)

        if response != 200:
            current_app.logger.error('Error sending review email {}, for {}'.format(email.id, magazine.id))

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
            topics=data['topics']
        )

        if 'pdf_data' in data:
            storage = Storage(current_app.config['STORAGE'])

            storage.upload_blob_from_base64string(
                data['filename'],
                magazine.filename,
                data['pdf_data'],
                content_type='application/pdf'
            )

        dao_update_record(Magazine, id=id, title=magazine.title, filename=magazine.filename)

        return jsonify(magazine.serialize()), 200

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
