from datetime import datetime, timedelta
import json
import os
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request
)
from urllib.parse import unquote

from flask_jwt_extended import jwt_required
from sqlalchemy.orm.exc import NoResultFound
from html.parser import HTMLParser

from app.na_celery import email_tasks
from app.comms.email import get_email_html, send_email, send_smtp_email
from app.dao.emails_dao import (
    dao_create_email,
    dao_create_email_to_member,
    dao_get_approved_emails_for_sending,
    dao_get_future_emails,
    dao_get_latest_emails,
    dao_get_email_by_id,
    dao_get_email_by_magazine_id,
    dao_get_emails_for_year_starting_on,
    dao_update_email,
)
from app.dao.magazines_dao import dao_get_magazine_by_id
from app.dao.users_dao import dao_get_admin_users, dao_get_users
from app.dao.events_dao import dao_get_event_by_old_id, dao_get_event_by_id

from app.errors import register_errors, InvalidRequest

from app.models import (
    Email, EmailToMember, Member,
    ANON_REMINDER, ANNOUNCEMENT, EVENT, MAGAZINE, MANAGED_EMAIL_TYPES, READY, APPROVED, REJECTED
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
    data = json.loads(unquote(request.args.get('data')))

    validate(data, post_preview_email_schema)

    current_app.logger.info('Email preview: {}'.format(data))

    html = get_email_html(**data)
    return html


@emails_blueprint.route('/email', methods=['POST'])
@jwt_required()
def create_email():
    data = request.get_json(force=True)

    validate(data, post_create_email_schema)

    email = Email(**data)

    dao_create_email(email)

    return jsonify(email.serialize()), 201


@emails_blueprint.route('/email/<uuid:email_id>', methods=['POST'])
@jwt_required()
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
            # send email to admin users and ask them to log in in order to approve the email
            review_part = '<div>Please review this email: {}/emails/{}</div>'.format(
                current_app.config['FRONTEND_ADMIN_URL'], str(email.id))

            subject = None
            if email.email_type == EVENT:
                event = dao_get_event_by_id(email.event_id)
                subject = 'Please review {}'.format(event.title)

                event_html = get_email_html(**data)
                response = send_smtp_email(emails_to, subject, review_part + event_html)
            elif email.email_type == MAGAZINE:
                magazine = dao_get_magazine_by_id(email.magazine_id)
                subject = 'Please review {}'.format(magazine.title)

                magazine_html = get_email_html(MAGAZINE, magazine_id=magazine.id)
                response = send_smtp_email(emails_to, subject, review_part + magazine_html)
        elif data.get('email_state') == REJECTED:
            dao_update_email(email_id, email_state=REJECTED)

            message = '<div>Please correct this email <a href="{}">{}</a></div>'.format(
                '{}/emails/{}'.format(current_app.config['FRONTEND_ADMIN_URL'], str(email.id)),
                email.get_subject())

            message += '<div>Reason: {}</div>'.format(data.get('reject_reason'))

            response = send_smtp_email(emails_to, '{} email needs to be corrected'.format(event.title), message)
        elif data.get('email_state') == APPROVED:
            later = datetime.utcnow() + timedelta(hours=current_app.config['EMAIL_DELAY'])
            if later < email.send_starts_at:
                later = email.send_starts_at + timedelta(hours=9)

            dao_update_email(email_id, send_after=later)

            review_part = '<div>Email will be sent after {}, log in to reject: {}/emails/{}</div>'.format(
                later.strftime("%d/%m/%Y %H:%M"), current_app.config['FRONTEND_ADMIN_URL'], str(email.id))

            if email.email_type == EVENT:
                event_html = get_email_html(**data)
                response = send_smtp_email(
                    emails_to, "{} has been approved".format(email.get_subject()), review_part + event_html)
        email_json = email.serialize()
        if response:
            email_json['email_status_code'] = response
        return jsonify(email_json), 200

    raise InvalidRequest('{} did not update email'.format(email_id), 400)


@emails_blueprint.route('/email/types', methods=['GET'])
@jwt_required()
def get_email_types():
    return jsonify([{'type': email_type} for email_type in MANAGED_EMAIL_TYPES])


@emails_blueprint.route('/email/default_details/<uuid:event_id>', methods=['GET'])
@jwt_required()
def get_default_details(event_id):
    event = dao_get_event_by_id(event_id)
    fees = f"<div><strong>Fees:</strong> £{event.fee}, £{event.conc_fee} concession for students, "\
        "income support & OAPs, and free for members of New Acropolis.</div>"
    if event.fee == 0:
        fees = "<div><strong>Fees:</strong> Free Admission</div>"
    elif event.fee == -2:
        fees = "<div><strong>Fees:</strong> External site</div>"
    elif event.fee == -3:
        fees = "<div><strong>Fees:</strong> Donation</div>"
    details = f"{fees}<div><strong>Venue:</strong> {event.venue.address}</div>{event.venue.directions}"

    return jsonify({'details': details})


@emails_blueprint.route('/emails/future', methods=['GET'])
@jwt_required()
def get_future_emails():
    emails = dao_get_future_emails()

    return jsonify([e.serialize() for e in emails])


@emails_blueprint.route('/emails/latest', methods=['GET'])
@jwt_required()
def get_latest_emails():
    emails = dao_get_latest_emails()

    return jsonify([e.serialize() for e in emails])


@emails_blueprint.route('/emails/import', methods=['POST'])
@jwt_required()
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
                elif item['eventdetails'].startswith('Last chance to verify your email to restart your subscription'):
                    email_type = ANON_REMINDER
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
                expires = datetime.strptime(item['timestamp'], "%Y-%m-%d %H:%M:%S") + timedelta(weeks=2)

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

            if dao_create_email(email):
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
@jwt_required()
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
@jwt_required()
def send_message():
    data = request.get_json(force=True)
    current_app.logger.info('send_message: %r', data)

    validate(data, post_send_message_schema)

    emails_to = [user.email for user in dao_get_admin_users()]

    status_code = send_smtp_email(emails_to, 'Web message: {}'.format(
        data['reason']), data['message'], from_email=data['email'], from_name=data['name'])

    return jsonify(
        {'message': 'Your message was sent' if status_code == 200 else 'An error occurred sending your message'})


@emails_blueprint.route('/email/test')
@jwt_required()
def send_test_email():  # pragma:no cover
    current_app.logger.info('Sending test email...')
    res = send_smtp_email(
        current_app.config.get('TEST_EMAIL'),
        'Sending test email',
        '<h3>Test</h3> email body',
        from_email=current_app.config.get('TEST_EMAIL').replace("@", f"+{current_app.config.get('ENVIRONMENT')}@"),
        from_name=f"Test+{current_app.config.get('ENVIRONMENT')}"
    )

    return 'ok' if res == 200 else 'error'


@emails_blueprint.route('/email/send/<uuid:email_id>')
@jwt_required()
def send_email_by_id(email_id):  # pragma:no cover
    current_app.logger.info(f'Sending email by id: {email_id}')
    from app.na_celery.email_tasks import send_emails as send_email_task
    try:
        send_email_task(email_id)
        return 'Sent email'
    except Exception as e:
        return f'Error sending email: {str(e)}'


@emails_blueprint.route('/emails/approved')
@jwt_required()
def get_approved_emails():
    emails = dao_get_approved_emails_for_sending()

    return jsonify([e.serialize() for e in emails])
