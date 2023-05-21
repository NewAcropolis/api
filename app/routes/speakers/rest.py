from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)
from flask_jwt_extended import jwt_required

from app.dao.speakers_dao import (
    dao_get_speakers, dao_get_speaker_by_id, dao_get_speaker_by_name, dao_create_speaker, dao_update_speaker
)
from app.errors import register_errors
from app.models import Speaker
from app.schema_validation import validate
from app.routes.speakers.schemas import (
    post_create_speaker_schema,
    post_create_speakers_schema,
    post_import_speakers_schema,
    post_update_speaker_schema
)

speakers_blueprint = Blueprint('speakers', __name__)
speaker_blueprint = Blueprint('speaker', __name__)

register_errors(speakers_blueprint)
register_errors(speaker_blueprint)


@speakers_blueprint.route('/speakers')
@jwt_required()
def get_speakers():
    speakers = [s.serialize() if s else None for s in dao_get_speakers()]
    return jsonify(speakers)


@speakers_blueprint.route('/speakers', methods=['POST'])
@jwt_required()
def create_speakers():
    data = request.get_json(force=True)

    validate(data, post_create_speakers_schema)

    speakers = []
    for item in data:
        speaker = Speaker.query.filter(Speaker.name == item['name']).first()
        if not speaker:
            speaker = Speaker(**item)
            speakers.append(speaker)
            dao_create_speaker(speaker)
        else:
            current_app.logger.info('speaker already exists: {}'.format(speaker.name))
    return jsonify([s.serialize() for s in speakers]), 201


@speakers_blueprint.route('/speakers/import', methods=['POST'])
@jwt_required()
def import_speakers():
    data = request.get_json(force=True)

    validate(data, post_import_speakers_schema)

    errors = []
    speakers = []
    for item in data:
        err = ''
        if item.get('parent_name'):
            parent_speaker = Speaker.query.filter(Speaker.name == item['parent_name']).first()
            if parent_speaker:
                if parent_speaker.parent_id:
                    err = 'Parent speaker can`t have a parent'
                    current_app.logger.error(err)
                    errors.append(err)
                else:
                    item['parent_id'] = str(parent_speaker.id)
            else:
                err = 'Can`t find speaker: {}'.format(item['parent_name'])
                current_app.logger.error(err)
                errors.append(err)
            del item['parent_name']

        if not err:
            speaker = Speaker.query.filter(Speaker.name == item['name']).first()
            if not speaker:
                speaker = Speaker(**item)
                speakers.append(speaker)
                dao_create_speaker(speaker)
            else:
                err = u'speaker already exists: {}'.format(speaker.name)
                current_app.logger.error(err)
                errors.append(err)

    res = {
        "speakers": [s.serialize() for s in speakers]
    }

    if errors:
        res['errors'] = errors

    return jsonify(res), 201 if speakers else 400 if errors else 200


@speaker_blueprint.route('/speaker/<uuid:speaker_id>', methods=['GET'])
@jwt_required()
def get_speaker_by_id(speaker_id):
    current_app.logger.info('get_speaker: {}'.format(speaker_id))
    speaker = dao_get_speaker_by_id(speaker_id)
    return jsonify(speaker.serialize())


@speaker_blueprint.route('/speaker', methods=['POST'])
@jwt_required()
def create_speaker():
    data = request.get_json(force=True)

    validate(data, post_create_speaker_schema)

    db_speaker = dao_get_speaker_by_name(data.get('name'))
    if db_speaker:
        current_app.logger.info('Speaker found: {}'.format(db_speaker.id))
        return jsonify(db_speaker.serialize()), 200

    speaker = Speaker(**data)

    dao_create_speaker(speaker)
    current_app.logger.info('Speaker created: {}'.format(speaker.id))
    return jsonify(speaker.serialize()), 201


@speaker_blueprint.route('/speaker/<uuid:speaker_id>', methods=['POST'])
@jwt_required()
def update_speaker(speaker_id):
    data = request.get_json()

    validate(data, post_update_speaker_schema)

    speaker = dao_get_speaker_by_id(speaker_id)

    dao_update_speaker(speaker_id, **data)

    return jsonify(speaker.serialize()), 200
