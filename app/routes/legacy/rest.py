import StringIO
from flask import Blueprint, current_app, jsonify, request, send_file
from sqlalchemy.orm.exc import NoResultFound

from app.dao.events_dao import dao_get_event_by_old_id
from app.errors import register_errors, InvalidRequest
from app.utils.storage import Storage

legacy_blueprint = Blueprint('legacy', __name__)
register_errors(legacy_blueprint)


@legacy_blueprint.route('/legacy/image_handler', methods=['GET'])
def image_handler():
    # ignore leading events part for event images
    imagefile = '/'.join(request.args.get('imagefile').split('/')[1:])

    if 'w' not in request.args.keys() and 'h' not in request.args.keys():
        image_size = 'standard/'
    else:
        image_size = 'thumbnail/'

    storage = Storage(current_app.config['STORAGE'])

    img = StringIO.StringIO(storage.get_blob(image_size + imagefile))
    return send_file(img, mimetype='image/jpeg')


@legacy_blueprint.route('/legacy/event_handler', methods=['GET'])
def event_handler():
    old_id = request.args.get('eventid')

    try:
        int(old_id)
    except:
        raise InvalidRequest('invalid event old_id: {}'.format(old_id), 400)

    event = dao_get_event_by_old_id(old_id)

    if not event:
        raise InvalidRequest('event not found for old_id: {}'.format(old_id), 404)

    return jsonify(event.serialize())
