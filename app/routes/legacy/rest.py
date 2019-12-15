import StringIO
from flask import Blueprint, current_app, request, send_file

from app.utils.storage import Storage

legacy_blueprint = Blueprint('legacy', __name__)


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
