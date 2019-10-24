from datetime import datetime, timedelta
import json
import os
from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request
)
import urlparse

from flask_jwt_extended import jwt_required
from sqlalchemy.orm.exc import NoResultFound
from HTMLParser import HTMLParser

from app.na_celery import email_tasks, revoke_task
from app.comms.email import get_email_html, send_email
from app.dao.emails_dao import (
    dao_create_email,
    dao_create_email_to_member,
    dao_get_future_emails,
    dao_get_latest_emails,
    dao_add_member_sent_to_email,
    dao_get_email_by_id,
    dao_get_emails_for_year_starting_on,
    dao_update_email,
)

from app.dao.users_dao import dao_get_admin_users, dao_get_users
from app.dao.events_dao import dao_get_event_by_old_id, dao_get_event_by_id

from app.comms.email import get_nice_event_dates
from app.errors import register_errors, InvalidRequest

from app.models import (
    Email, EmailToMember, Member,
    ANNOUNCEMENT, EVENT, MAGAZINE, MANAGED_EMAIL_TYPES, READY, APPROVED, REJECTED
)
from app.routes.emails.schemas import (
    post_create_email_schema, post_update_email_schema, post_import_emails_schema, post_preview_email_schema,
    post_import_email_members_schema, post_send_message_schema
)
from app.schema_validation import validate

emails_blueprint = Blueprint('emails', __name__)
register_errors(emails_blueprint)


@emails_blueprint.route('/email/preview', methods=['GET'])
def email_preview():
    data = json.loads(urlparse.unquote(request.args.get('data')))

    validate(data, post_preview_email_schema)

    current_app.logger.info('Email preview: {}'.format(data))

    html = get_email_html(**data)
    return html


@emails_blueprint.route('/email', methods=['POST'])
@jwt_required
def create_email():
    data = request.get_json(force=True)

    validate(data, post_create_email_schema)

    email = Email(**data)

    dao_create_email(email)

    return jsonify(email.serialize()), 201


@emails_blueprint.route('/email/<uuid:email_id>', methods=['POST'])
@jwt_required
def update_email(email_id):
    data = request.get_json(force=True)

    validate(data, post_update_email_schema)

    if data['email_type'] == EVENT:
        try:
            event = dao_get_event_by_id(data.get('event_id'))
        except NoResultFound:
            raise InvalidRequest('event not found: {}'.format(data.get('event_id')), 400)

    email_data = {}
    for k in data.keys():
        if hasattr(Email, k):
            email_data[k] = data[k]

    current_app.logger.info('Update email: {}'.format(email_data))

    res = dao_update_email(email_id, **email_data)

    if res:
        email = dao_get_email_by_id(email_id)
        response = None
        emails_to = [user.email for user in dao_get_users()]

        if data.get('email_state') == READY:
            subject = None
            if data['email_type'] == EVENT:
                event = dao_get_event_by_id(data.get('event_id'))
                subject = 'Please review {}'.format(event.title)

            # send email to admin users and ask them to log in in order to approve the email
            review_part = '<div>Please review this email: {}/emails/{}</div>'.format(
                current_app.config['FRONTEND_ADMIN_URL'], str(email.id))
            event_html = get_email_html(**data)
            response = send_email(emails_to, subject, review_part + event_html)
        elif data.get('email_state') == REJECTED:
            dao_update_email(email_id, email_state=REJECTED)

            message = '<div>Please correct this email <a href="{}">{}</a></div>'.format(
                '{}/emails/{}'.format(current_app.config['FRONTEND_ADMIN_URL'], str(email.id)),
                email.get_subject())

            message += '<div>Reason: {}</div>'.format(data.get('reject_reason'))

            response = send_email(emails_to, '{} email needs to be corrected'.format(event.title), message)
        elif data.get('email_state') == APPROVED:
            later = datetime.utcnow() + timedelta(hours=current_app.config['EMAIL_DELAY'])
            if later < email.send_starts_at:
                later = email.send_starts_at + timedelta(hours=9)

            dao_update_email(email_id, send_after=later)

            review_part = '<div>Email will be sent after {}, log in to reject: {}/emails/{}</div>'.format(
                later.strftime("%d/%m/%Y %H:%M"), current_app.config['FRONTEND_ADMIN_URL'], str(email.id))
            event_html = get_email_html(**data)
            response = send_email(
                emails_to, "{} has been approved".format(email.get_subject()), review_part + event_html)

        email_json = email.serialize()
        if response:
            email_json['email_status_code'] = response
        return jsonify(email_json), 200

    raise InvalidRequest('{} did not update email'.format(email_id), 400)


@emails_blueprint.route('/email/types', methods=['GET'])
@jwt_required
def get_email_types():
    return jsonify([{'type': email_type} for email_type in MANAGED_EMAIL_TYPES])


@emails_blueprint.route('/emails/future', methods=['GET'])
@jwt_required
def get_future_emails():
    emails = dao_get_future_emails()

    return jsonify([e.serialize() for e in emails])


@emails_blueprint.route('/emails/latest', methods=['GET'])
@jwt_required
def get_latest_emails():
    emails = dao_get_latest_emails()

    return jsonify([e.serialize() for e in emails])


@emails_blueprint.route('/emails/import', methods=['POST'])
@jwt_required
def import_emails():
    data = request.get_json(force=True)

    validate(data, post_import_emails_schema)

    errors = []
    emails = []
    for item in data:
        err = ''
        email = Email.query.filter(Email.old_id == item['id']).first()
        if not email:
            event_id = None
            email_type = EVENT
            if int(item['eventid']) < 0:
                if item['eventdetails'].startswith('New Acropolis'):
                    email_type = MAGAZINE
                else:
                    email_type = ANNOUNCEMENT

            expires = None
            if email_type == EVENT:
                event = dao_get_event_by_old_id(item['eventid'])

                if not event:
                    err = u'event not found: {}'.format(item)
                    current_app.logger.info(err)
                    errors.append(err)
                    continue
                event_id = str(event.id)
                expires = event.get_last_event_date()
            else:
                # default to 2 weeks expiry after email was created
                expires = datetime.strptime(item['timestamp'], "%Y-%m-%d %H:%M") + timedelta(weeks=2)

            email = Email(
                event_id=event_id,
                old_id=item['id'],
                old_event_id=item['eventid'],
                details=item['eventdetails'],
                extra_txt=item['extratxt'],
                replace_all=True if item['replaceAll'] == 'y' else False,
                email_type=email_type,
                created_at=item['timestamp'],
                send_starts_at=item['timestamp'],
                expires=expires
            )

            dao_create_email(email)
            emails.append(email)
        else:
            err = u'email already exists: {}'.format(email.old_id)
            current_app.logger.info(err)
            errors.append(err)

    res = {
        "emails": [e.serialize() for e in emails]
    }

    if errors:
        res['errors'] = errors

    return jsonify(res), 201 if emails else 400 if errors else 200


@emails_blueprint.route('/emails/members/import', methods=['POST'])
@jwt_required
def import_emails_members_sent_to():
    data = request.get_json(force=True)

    validate(data, post_import_email_members_schema)

    errors = []
    emails_to_members = []
    for i, item in enumerate(data):
        email = Email.query.filter_by(old_id=item['emailid']).first()
        member = Member.query.filter_by(old_id=item['mailinglistid']).first()

        if not email:
            error = '{}: Email not found: {}'.format(i, item['emailid'])
            errors.append(error)
            current_app.logger.error(error)

        if not member:
            error = '{}: Member not found: {}'.format(i, item['emailid'])
            errors.append(error)
            current_app.logger.error(error)

        if email and member:
            email_to_member_found = EmailToMember.query.filter_by(email_id=email.id, member_id=member.id).first()

            if email_to_member_found:
                error = '{}: Already exists email_to_member {}, {}'.format(i, str(email.id), str(member.id))
                current_app.logger.error(error)
                errors.append(error)
                continue

            email_to_member = EmailToMember(
                email_id=email.id,
                member_id=member.id,
                created_at=item['timestamp']
            )
            dao_create_email_to_member(email_to_member)
            emails_to_members.append(email_to_member)
            current_app.logger.info('%s: Adding email_to_member %s, %s', i, str(email.id), str(member.id))

    res = {
        "emails_members_sent_to": [e.serialize() for e in emails_to_members]
    }

    if errors:
        res['errors'] = errors

    return jsonify(res), 201 if emails_to_members else 400 if errors else 200


@emails_blueprint.route('/send_message', methods=['POST'])
@jwt_required
def send_message():
    data = request.get_json(force=True)
    current_app.logger.info('send_message: %r', data)

    validate(data, post_send_message_schema)

    emails_to = [user.email for user in dao_get_admin_users()]

    send_email(emails_to, 'Web message: {}'.format(
        data['reason']), data['message'], _from='{}<{}>'.format(data['name'], data['email']))
    return jsonify({'message': 'Your message was sent'})
