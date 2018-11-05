import os
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)
import re

from flask_jwt_extended import jwt_required

from app.dao.events_dao import dao_create_event, dao_get_events, dao_update_event
from app.dao.event_dates_dao import dao_create_event_date
from app.dao.event_types_dao import dao_get_event_type_by_old_id
from app.dao.speakers_dao import dao_get_speaker_by_name
from app.dao.venues_dao import dao_get_venue_by_old_id

from app.errors import register_errors, InvalidRequest
from app.models import Event, EventDate

from app.schema_validation import validate

from app.routes.events.schemas import post_import_events_schema

events_blueprint = Blueprint('events', __name__)
register_errors(events_blueprint)


@events_blueprint.route('/events')
def get_events():
    events = [e.serialize() if e else None for e in dao_get_events()]

    def extract_startdate(json):
        try:
            return json['event_dates'][0]['event_datetime']
        except KeyError:
            return 0

    events.sort(key=extract_startdate, reverse=True)
    return jsonify(events)


@events_blueprint.route('/events/future')
def get_future_events():
    pass


@events_blueprint.route('/events/past-year')
def get_past_year_events():
    pass


@events_blueprint.route('/events/extract-speakers', methods=['POST'])
def extract_speakers():
    data = request.get_json(force=True)
    validate(data, post_import_events_schema)

    speakers = []
    for item in data:
        speakers.append(item['Speaker'])

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
                venue_id=venue.id
            )

            def add_event_date(event_datetime):
                event_date = EventDate(
                    event_datetime=event_datetime,
                )

                dao_create_event_date(event_date, speakers)

                event.event_dates.append(event_date)

            add_event_date(item['StartDate'])

            for i in range(2, 5):
                if item['StartDate{}'.format(i)] > '0000-00-00 00:00:00':
                    add_event_date(item['StartDate{}'.format(i)])

            events.append(event)
            dao_create_event(event)
        else:
            err = u'event already exists: {} - {}'.format(event.old_id, event.title)
            current_app.logger.info(err)
            errors.append(err)

    res = {
        "events": [e.serialize() for e in events]
    }

    if errors:
        res['errors'] = errors

    return jsonify(res), 201 if events else 400 if errors else 200
