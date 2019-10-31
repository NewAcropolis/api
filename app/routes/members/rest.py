from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)
import json
from sqlalchemy.orm.exc import NoResultFound

from flask_jwt_extended import jwt_required

from app.dao.members_dao import (
    dao_create_member,
    dao_get_members,
    dao_get_member_by_email,
    dao_get_member_by_id,
    dao_update_member
)

from app.comms.email import get_email_html, send_email
from app.comms.encryption import decrypt, get_tokens
from app.errors import register_errors, InvalidRequest

from app.models import Marketing, Member, BASIC
from app.routes.members.schemas import post_import_members_schema, post_subscribe_member_schema
from app.schema_validation import validate

members_blueprint = Blueprint('members', __name__)
register_errors(members_blueprint)


@members_blueprint.route('/member/subscribe', methods=['POST'])
@jwt_required
def subscribe_member():
    data = request.get_json(force=True)

    current_app.logger.info('Subscribe member: {}'.format(data))

    validate(data, post_subscribe_member_schema)

    member = dao_get_member_by_email(data.get('email'))

    if member:
        return jsonify({'error': 'member already subscribed: {}'.format(member.email)}), 400

    member = Member(
        name=data['name'],
        email=data['email'],
        marketing_id=data['marketing_id'],
        active=True
    )

    dao_create_member(member)

    basic_html = get_email_html(
        email_type=BASIC,
        title='Subscription',
        message="Thank you{} for subscribing to New Acropolis events and news letters".format(
            ' {}'.format(data.get('name', '')) if 'name' in data else ''
        ))
    response = send_email(data['email'], 'New Acropolis subscription', basic_html)

    return jsonify(member.serialize())


@members_blueprint.route('/member/unsubscribe/<unsubcode>', methods=['POST'])
@jwt_required
def unsubscribe_member(unsubcode):
    tokens = get_tokens(decrypt(unsubcode, current_app.config['EMAIL_UNSUB_SALT']))
    member = dao_get_member_by_id(tokens[current_app.config['EMAIL_TOKENS']['member_id']])
    dao_update_member(member.id, active=False)

    return jsonify({'message': '{} unsubscribed'.format(member.name)})


@members_blueprint.route('/members', methods=['GET'])
@jwt_required
def get_members():
    members = [m.serialize() for m in dao_get_members()]

    return jsonify(members)


@members_blueprint.route('/members/import', methods=['POST'])
@jwt_required
def import_members():
    text = request.get_data(as_text=True)
    text = text.replace('"EmailAdd": "anon"', '"EmailAdd": null')
    text = text.replace('"EmailAdd": ""', '"EmailAdd": null')
    text = text.replace('"CreationDate": "0000-00-00"', '"CreationDate": null')
    data = json.loads(text)

    validate(data, post_import_members_schema)

    errors = []
    members = []
    for item in data:
        err = ''
        member = Member.query.filter(Member.old_id == item['id']).first()

        if member:
            err = u'member already exists: {}'.format(member.old_id)
            current_app.logger.info(err)
            errors.append(err)
        else:
            member = Member(
                old_id=item['id'],
                name=item['Name'],
                email=item['EmailAdd'],
                active=item["Active"] == "y",
                created_at=item["CreationDate"],
                old_marketing_id=item["Marketing"],
                is_course_member=item["IsMember"] == "y",
                last_updated=item["LastUpdated"]
            )

            marketing = Marketing.query.filter(Marketing.old_id == item['Marketing']).first()
            if not marketing:
                err = "Cannot find marketing: {}".format(item['Marketing'])
                current_app.logger.error(err)
                errors.append(err)
                continue
            else:
                member.marketing_id = marketing.id

            dao_create_member(member)
            members.append(member)

            current_app.logger.info('Creating member: %d, %s', member.old_id, member.name)

    res = {
        "members": [m.serialize() for m in members]
    }

    if errors:
        res['errors'] = errors

    return jsonify(res), 201 if members else 400 if errors else 200
