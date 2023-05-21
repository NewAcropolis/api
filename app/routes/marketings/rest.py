from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)

from flask_jwt_extended import jwt_required

from app.dao.marketings_dao import (
    dao_create_marketing,
    dao_get_marketings,
)

from app.errors import register_errors

from app.models import Marketing
from app.routes.marketings.schemas import post_import_marketings_schema
from app.schema_validation import validate

marketings_blueprint = Blueprint('marketings', __name__)
register_errors(marketings_blueprint)


@marketings_blueprint.route('/marketings', methods=['GET'])
@jwt_required()
def get_marketings():
    marketings = dao_get_marketings()
    return jsonify([m.serialize() for m in marketings])


@marketings_blueprint.route('/marketings/import', methods=['POST'])
@jwt_required()
def import_marketings():
    data = request.get_json(force=True)

    validate(data, post_import_marketings_schema)

    errors = []
    marketings = []
    for item in data:
        err = ''
        marketing = Marketing.query.filter(Marketing.old_id == item['id']).first()

        if marketing:
            err = u'marketing already exists: {}'.format(marketing.old_id)
            current_app.logger.info(err)
            errors.append(err)
        else:
            marketing = Marketing(
                old_id=item['id'],
                description=item['marketingtxt'],
                order_number=item['ordernum'],
                active=item["visible"] == "1"
            )

            dao_create_marketing(marketing)
            marketings.append(marketing)

    res = {
        "marketings": [m.serialize() for m in marketings]
    }

    if errors:
        res['errors'] = errors

    return jsonify(res), 201 if marketings else 400 if errors else 200
