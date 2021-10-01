from datetime import datetime
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)
import os.path
import re
import time

from flask_jwt_extended import jwt_required
from sqlalchemy.orm.exc import NoResultFound

from app.comms.email import get_email_html, send_email, send_smtp_email
from app.dao.events_dao import (
    dao_create_event,
    dao_create_reserve_place,
    dao_has_reserved_place,
    dao_get_reserved_places,
    dao_delete_event,
    dao_get_events,
    dao_get_event_by_id,
    dao_get_events_in_year,
    dao_get_future_events,
    dao_get_limited_events,
    dao_get_past_year_events,
    dao_update_event,
)
from app.dao.event_dates_dao import dao_create_event_date, dao_get_event_date_by_id
from app.dao.event_types_dao import dao_get_event_type_by_old_id, dao_get_event_type_by_id
from app.dao.reject_reasons_dao import dao_create_reject_reason, dao_update_reject_reason
from app.dao.speakers_dao import dao_get_speaker_by_name, dao_get_speaker_by_id
from app.dao.tickets_dao import dao_get_tickets_for_event_date
from app.dao.users_dao import dao_get_admin_users, dao_get_users
from app.dao.venues_dao import dao_get_venue_by_old_id, dao_get_venue_by_id

from app.errors import register_errors, InvalidRequest, PaypalException
from app.models import Event, EventDate, RejectReason, ReservedPlace, APPROVED, DRAFT, READY, REJECTED, BASIC

from app.na_celery import paypal_tasks
from app.routes import is_running_locally
from app.routes.events.schemas import (
    post_create_event_schema, post_update_event_schema, post_import_events_schema,
    post_reserve_place_schema
)

from app.schema_validation import validate

from app.payments.paypal import PayPal
from app.utils.storage import Storage

events_blueprint = Blueprint('events', __name__)
register_errors(events_blueprint)


def extract_startdate(json):
    return json['event_dates'][0]['event_datetime'] if 'event_dates' in json else 0


@events_blueprint.route('/paypal/<item_id>', methods=['POST'])
@jwt_required
def create_test_paypal(item_id):
    if current_app.config['ENVIRONMENT'] == 'live':
        return 'Cannot test paypal on live environment'

    p = PayPal()
    button_id = p.create_update_paypal_button(item_id, 'test paypal')

    return button_id


@events_blueprint.route('/event', methods=['POST'])
@jwt_required
def create_event():
    data = request.get_json(force=True)
    event_year = None

    validate(data, post_create_event_schema)

    try:
        dao_get_event_type_by_id(data['event_type_id'])
    except NoResultFound:
        raise InvalidRequest('event type not found: {}'.format(data['event_type_id']), 400)

    try:
        dao_get_venue_by_id(data['venue_id'])
    except NoResultFound:
        raise InvalidRequest('venue not found: {}'.format(data['venue_id']), 400)

    event = Event(
        event_type_id=data['event_type_id'],
        title=data['title'],
        sub_title=data.get('sub_title'),
        description=data['description'],
        booking_code='',
        fee=data.get('fee'),
        conc_fee=data.get('conc_fee'),
        multi_day_fee=data.get('multi_day_fee'),
        multi_day_conc_fee=data.get('multi_day_conc_fee'),
        venue_id=data.get('venue_id'),
        event_state=data.get('event_state', DRAFT),
        remote_access=data.get('remote_access'),
        remote_pw=data.get('remote_pw'),
    )

    for event_date in data.get('event_dates'):
        if not event_year:
            event_year = event_date['event_date'].split('-')[0]
        speakers = []
        for s in event_date.get('speakers', []):
            speaker = dao_get_speaker_by_id(s['speaker_id'])
            speakers.append(speaker)

        e = EventDate(
            event_datetime=event_date['event_date'],
            end_time=None if event_date.get('end_time') == '' else event_date.get('end_time'),
            speakers=speakers
        )

        dao_create_event_date(e)
        event.event_dates.append(e)

    dao_create_event(event)

    image_filename = data.get('image_filename')

    image_data = data.get('image_data')

    storage = Storage(current_app.config['STORAGE'])

    if image_data:
        target_image_filename = '{}/{}'.format(event_year, str(event.id))

        storage.upload_blob_from_base64string(image_filename, target_image_filename, image_data)

        image_filename = target_image_filename
    elif image_filename:
        if not storage.blob_exists(image_filename):
            raise InvalidRequest('{} does not exist'.format(image_filename), 400)

    event.image_filename = image_filename
    dao_update_event(event.id, image_filename=image_filename)

    if event.fee and event.fee > 0 and event.event_state in [READY, APPROVED]:
        paypal_tasks.create_update_paypal_button_task.apply_async((str(event.id),))

    return jsonify(event.serialize()), 201


@events_blueprint.route('/event/<uuid:event_id>', methods=['DELETE'])
@jwt_required
def delete_event(event_id):
    dao_delete_event(event_id)

    try:
        event = dao_get_event_by_id(event_id)
        if event:
            raise InvalidRequest("{} was not deleted".format(event_id), 500)
    except NoResultFound:
        current_app.logger.info('{} deleted'.format(event_id))

    return jsonify({'message': '{} deleted'.format(event_id)}), 200


@events_blueprint.route('/event/<uuid:event_id>', methods=['POST'])
@jwt_required
def update_event(event_id):
    data = request.get_json(force=True)

    current_app.logger.info('Update event: {}'.format(data))

    validate(data, post_update_event_schema)

    try:
        event = dao_get_event_by_id(event_id)
    except NoResultFound:
        raise InvalidRequest('event not found: {}'.format(event_id), 400)

    errs = []
    event_dates = []
    event_data = {}

    if data.get('event_state') == REJECTED:
        new_rejects = [r for r in data.get('reject_reasons') if not r.get('id')]
        if not new_rejects:
            raise InvalidRequest('rejected event requires new reject reason', 400)
    elif data.get('event_state') == APPROVED:
        if data.get('reject_reasons'):
            rejects = [r for r in data.get('reject_reasons') if not r.get('resolved')]
            if rejects:
                raise InvalidRequest('approved event should not have any reject reasons', 400)

    data_event_dates = data.get('event_dates')

    if data_event_dates:
        serialized_event_dates = event.serialize_event_dates()

        data_event_dates__dates = [e['event_date'] for e in data_event_dates]
        serialized_event_dates__dates = [e['event_datetime'] for e in serialized_event_dates]

        diff_add = set(data_event_dates__dates).difference(serialized_event_dates__dates)
        intersect = set(data_event_dates__dates).intersection(serialized_event_dates__dates)

        dates_to_add = [e for e in data_event_dates if e['event_date'] in diff_add]
        dates_to_update = [e for e in data_event_dates if e['event_date'] in intersect]

        for _date in dates_to_add:
            speakers = []
            for s in _date.get('speakers', []):
                speaker = dao_get_speaker_by_id(s['speaker_id'])
                speakers.append(speaker)

            e = EventDate(
                event_id=event_id,
                event_datetime=_date['event_date'],
                end_time=_date.get('end_time'),
                speakers=speakers
            )

            current_app.logger.info('Adding event date: {}'.format(_date['event_date']))

            dao_create_event_date(e)

            if _date['event_date'] not in [_e.event_datetime for _e in event_dates]:
                event_dates.append(e)

        for _date in sorted(dates_to_update, key=lambda k: k['event_date']):
            speakers = []
            for s in _date['speakers']:
                speaker = dao_get_speaker_by_id(s['speaker_id'])
                speakers.append(speaker)
            db_event_date = [
                e for e in event.event_dates if e.event_datetime.strftime('%Y-%m-%d %H:%M') == _date['event_date']][0]
            db_event_date.speakers = speakers

            if _date['event_date'] not in [_e.event_datetime for _e in event_dates]:
                event_dates.append(db_event_date)

    if data.get('reject_reasons'):
        for reject_reason in data.get('reject_reasons'):
            if reject_reason.get('id'):
                reject_data = {
                    'reason': reject_reason['reason'],
                    'resolved': reject_reason.get('resolved') or False
                }

                dao_update_reject_reason(reject_reason.get('id'), **reject_data)
            else:
                rr = RejectReason(
                    event_id=event_id,
                    reason=reject_reason['reason'],
                    resolved=reject_reason.get('resolved') or False,
                    created_by=reject_reason.get('created_by')
                )
                dao_create_reject_reason(rr)

    event_data = {}
    for k in data.keys():
        if hasattr(Event, k) and k not in ['reject_reasons']:
            event_data[k] = data[k]

    if event_dates:
        event_data['event_dates'] = event_dates
    elif data_event_dates == []:
        raise InvalidRequest('{} needs an event date'.format(event_id), 400)

    if event_data.get('fee') and event_data.get('fee') > 0:
        update_data = {
            'fee': event_data.get('fee'),
            'conc_fee': event_data.get('conc_fee'),
            'multi_day_fee': event_data.get('multi_day_fee') or 0,
            'multi_day_conc_fee': event_data.get('multi_day_conc_fee') or 0,
            'event_type_id': event_data.get('event_type_id'),
        }
        db_data = {
            'fee': event.fee,
            'conc_fee': event.conc_fee,
            'multi_day_fee': event.multi_day_fee,
            'multi_day_conc_fee': event.multi_day_conc_fee,
            'event_type_id': str(event.event_type.id),
        }

        if update_data != db_data:
            if data.get('event_state') in [READY, APPROVED]:
                paypal_tasks.create_update_paypal_button_task.apply_async((str(event_id),))

    res = dao_update_event(event_id, **event_data)

    if res:
        image_data = data.get('image_data')

        image_filename = data.get('image_filename')

        if current_app.config['STORAGE'].startswith('None'):
            current_app.logger.warn('Storage not setup')
        else:
            storage = Storage(current_app.config['STORAGE'])
            if image_data:
                event_year = str(event.event_dates[0].event_datetime).split('-')[0]
                target_image_filename = '{}/{}'.format(event_year, str(event_id))

                if data.get('event_state') != APPROVED:
                    target_image_filename += '-temp'

                storage.upload_blob_from_base64string(image_filename, target_image_filename, image_data)

                unix_time = time.time()
                image_filename = '{}?{}'.format(target_image_filename, unix_time)
            elif image_filename:
                image_filename_without_cache_buster = image_filename.split('?')[0]
                if not storage.blob_exists(image_filename_without_cache_buster):
                    raise InvalidRequest('{} does not exist'.format(image_filename_without_cache_buster), 400)

        if image_filename:
            if data.get('event_state') == APPROVED:
                if '-temp' in image_filename:
                    q_pos = image_filename.index('-temp?')
                    image_filename = image_filename[0:q_pos]
                    storage.rename_image(image_filename + '-temp', image_filename)
                else:
                    current_app.logger.warn(f"No temp file to rename: {image_filename}")

            event.image_filename = image_filename
            dao_update_event(event.id, image_filename=image_filename)

        json_event = event.serialize()

        if data.get('event_state') == READY:
            emails_to = [admin.email for admin in dao_get_admin_users()]

            message = 'Please review this event for publishing <a href="{}">{}</a>'.format(
                '{}/events/{}'.format(current_app.config['FRONTEND_ADMIN_URL'], event_id),
                event.title
            )

            status_code = send_smtp_email(emails_to, '{} is ready for review'.format(event.title), message)
            if status_code != 200:
                errs.append(f"Problem sending admin email {status_code}")
        elif data.get('event_state') == REJECTED:
            emails_to = [user.email for user in dao_get_users()]

            message = '<div>Please correct this event <a href="{}">{}</a></div>'.format(
                '{}/events/{}'.format(current_app.config['FRONTEND_ADMIN_URL'], event_id),
                event.title)

            message += '<ol>'
            for reject_reason in [rr for rr in json_event.get('reject_reasons') if not rr.get('resolved')]:
                message += '<li>{}</li>'.format(reject_reason['reason'])
            message += '</ol>'

            status_code = send_smtp_email(emails_to, '{} event needs to be corrected'.format(event.title), message)
            if status_code != 200:
                errs.append(f"Problem sending smtp emails: {status_code}")

        json_event['errors'] = errs
        return jsonify(json_event), 200

    raise InvalidRequest('{} did not update event'.format(event_id), 400)


@events_blueprint.route('/events')
@jwt_required
def get_events():
    events = [e.serialize() if e else None for e in dao_get_events()]

    events.sort(key=extract_startdate)
    return jsonify(events)


@events_blueprint.route('/event/<uuid:event_id>')
@jwt_required
def get_event_by_id(event_id):
    event = dao_get_event_by_id(event_id)
    return jsonify(event.serialize())


@events_blueprint.route('/events/year/<int:year>')
@jwt_required
def get_events_in_year(year):
    events = [e.serialize() if e else None for e in dao_get_events_in_year(year)]

    events.sort(key=extract_startdate, reverse=True)
    return jsonify(events)


@events_blueprint.route('/events/limit/<int:limit>')
@jwt_required
def get_limited_events(limit):
    if limit > current_app.config['EVENTS_MAX']:
        raise InvalidRequest("{} is greater than events max".format(limit), 400)

    events = [e.serialize() if e else None for e in dao_get_limited_events(limit)]

    return jsonify(events)


@events_blueprint.route('/events/future')
@jwt_required
def get_future_events():
    events = [e.serialize() if e else None for e in dao_get_future_events()]

    events.sort(key=extract_startdate)
    return jsonify(events)


@events_blueprint.route('/events/past_year')
@jwt_required
def get_past_year_events():
    events = [e.serialize() if e else None for e in dao_get_past_year_events()]

    events.sort(key=extract_startdate)
    return jsonify(events)


@events_blueprint.route('/events/extract-speakers', methods=['POST'])
def extract_speakers():
    data = request.get_json(force=True)
    validate(data, post_import_events_schema)

    speakers = []
    for item in data:
        speakers.append(item['Speaker'])

    # python 3 update code?
    sorted_speakers = [{"name": s} for s in sorted(set(speakers))]

    return jsonify(sorted_speakers), 200


@events_blueprint.route('/events/import', methods=['POST'])
@jwt_required
def import_events():
    data = request.get_json(force=True)

    validate(data, post_import_events_schema)

    errors = []
    events = []
    for item in data:
        err = ''
        event = Event.query.filter(Event.old_id == item['id']).first()
        if not event:
            speakers = []

            event_type = dao_get_event_type_by_old_id(item['Type'])
            if not event_type:
                err = '{} event type not found: {}'.format(item['id'], item['Type'])
                current_app.logger.info(err)
                errors.append(err)

            if item['Speaker']:
                for s in re.split(r' and | & ', item['Speaker']):
                    speaker = dao_get_speaker_by_name(s)
                    if not speaker:
                        err = '{} speaker not found: {}'.format(item['id'], item['Speaker'])
                        current_app.logger.info(err)
                        errors.append(err)
                    else:
                        speakers.append(speaker)

            venue = dao_get_venue_by_old_id(item['venue'])
            if not venue:
                err = '{} venue not found: {}'.format(item['id'], item['venue'])
                current_app.logger.info(err)
                errors.append(err)

            if err:
                continue

            event = Event(
                old_id=item['id'],
                event_type_id=event_type.id,
                title=item['Title'],
                sub_title=item['SubTitle'],
                description=item['Description'],
                booking_code=item['BookingCode'],
                image_filename=item['ImageFilename'],
                fee=item['Fee'],
                conc_fee=item['ConcFee'],
                multi_day_fee=item['MultiDayFee'],
                multi_day_conc_fee=item['MultiDayConcFee'],
                duration=item['Duration'],
                venue_id=venue.id,
                event_state=APPROVED
            )

            def add_event_date(event_datetime):
                event_date = EventDate(
                    event_datetime=event_datetime,
                    duration=item['Duration'],
                    fee=item['Fee'],
                    conc_fee=item['ConcFee'],
                    multi_day_fee=item['MultiDayFee'],
                    multi_day_conc_fee=item['MultiDayConcFee'],
                    venue_id=venue.id
                )

                dao_create_event_date(event_date, speakers)

                event.event_dates.append(event_date)

            add_event_date(item['StartDate'])

            for i in range(2, 5):
                if item['StartDate{}'.format(i)] > '0000-00-00 00:00:00':
                    add_event_date(item['StartDate{}'.format(i)])

            events.append(event)
            dao_create_event(event)
            current_app.logger.info(u'added event {} - {}'.format(event.old_id, event.title))
        else:
            err = u'event already exists: {} - {}'.format(event.old_id, event.title)
            current_app.logger.info(err)
            errors.append(err)

        if is_running_locally() and item['ImageFilename'] and item['ImageFilename'] != '../spacer.gif':
            storage = Storage(current_app.config['STORAGE'])

            if not storage.blob_exists(item['ImageFilename']):
                fname = "./data/events/{}".format(item['ImageFilename'])
                if os.path.isfile(fname):
                    storage.upload_blob(fname, item['ImageFilename'])
                else:
                    err = '{} not found for {}'.format(fname, event.old_id)
                    current_app.logger.info(err)
                    errors.append(err)
            else:
                current_app.logger.info('{} found'.format(item['ImageFilename']))

    res = {
        "events": [e.serialize() for e in events]
    }

    if errors:
        res['errors'] = errors

    return jsonify(res), 201 if events else 400 if errors else 200


@events_blueprint.route('/event/reserve', methods=['POST'])
@jwt_required
def reserve_place():
    data = request.get_json(force=True)
    validate(data, post_reserve_place_schema)

    if dao_has_reserved_place(data['name'], data['email'], data['eventdate_id']):
        return jsonify(
            {
                "error": f"{data['name']} has already reserved a place"
            }
        )

    reserved_place = ReservedPlace(
        eventdate_id=data['eventdate_id'],
        name=data['name'],
        email=data['email']
    )
    current_app.logger.info("Reserved place %r", reserved_place.serialize())

    dao_create_reserve_place(reserved_place)

    reserved_place_json = reserved_place.serialize()

    message = f"{reserved_place_json['name']},<br>"\
        f"Thank you for your reservation of {reserved_place_json['event_title']} "\
        f"on {reserved_place_json['nice_event_date']}"

    message_html = get_email_html(BASIC, message=message)

    send_email(
        data['email'],
        f"Reserved place for: {reserved_place_json['event_title']}",
        message_html
    )

    return jsonify(reserved_place_json)


@events_blueprint.route('/event/tickets_and_reserved/<uuid:eventdate_id>', methods=['GET'])
@jwt_required
def get_tickets_and_reserved_places(eventdate_id):
    reserved_places = dao_get_reserved_places(eventdate_id)
    tickets = dao_get_tickets_for_event_date(eventdate_id)

    tickets_and_reserved_places = {
        "reserved_places": [r.serialize() for r in reserved_places],
        "tickets": [t.serialize() for t in tickets],
    }
    return jsonify(tickets_and_reserved_places)
