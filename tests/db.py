from app import db

from app.dao.blacklist_dao import store_token
from app.dao.events_dao import dao_create_event
from app.dao.event_dates_dao import dao_create_event_date
from app.dao.event_types_dao import dao_create_event_type
from app.dao.fees_dao import dao_create_fee
from app.dao.speakers_dao import dao_create_speaker
from app.dao.venues_dao import dao_create_venue
from app.models import Event, EventDate, EventType, Fee, Speaker, Venue


def create_event(
    title='test title',
    description='test description',
    event_type_id=None,
    fee=5,
    conc_fee=3,
    multi_day_fee=12,
    multi_day_conc_fee=10,
    old_id=1,
    event_dates=None
):
    if not event_type_id:
        event_type = create_event_type(event_type='workshop')
        event_type_id = str(event_type.id)
    data = {
        'old_id': old_id,
        'event_type_id': event_type_id,
        'title': title,
        'description': description,
        'fee': fee,
        'conc_fee': conc_fee,
        'multi_day_fee': multi_day_fee,
        'multi_day_conc_fee': multi_day_conc_fee,
    }
    event = Event(**data)

    # if event_dates:
    #     event.event_dates.extend([e for e in event_dates])

    dao_create_event(event)
    return event


def create_event_type(
        old_id=1,
        event_type='talk',
        event_desc='test talk',
        event_filename=None,
        duration=45,
        repeat=1,
        repeat_interval=0
):
    data = {
        'old_id': old_id,
        'event_type': event_type,
        'event_desc': event_desc,
        'event_filename': event_filename,
        'duration': duration,
        'repeat': repeat,
        'repeat_interval': repeat_interval
    }
    event_type = EventType(**data)

    dao_create_event_type(event_type)
    return event_type


def create_event_date(
    event_id=None,
    event_datetime='2018-01-01 19:00',
    duration=90,
    soldout=False,
    repeat=3,
    repeat_interval=7,
    fee=5,
    conc_fee=3,
    multi_day_fee=12,
    multi_day_conc_fee=10,
    speakers=None,
):
    venue = create_venue()
    if not event_id:
        event_type = create_event_type()
        event = create_event(event_type_id=str(event_type.id))
        event_id = event.id

    data = {
        'event_id': event_id,
        'event_datetime': event_datetime,
        'duration': duration,
        'soldout': soldout,
        'repeat': repeat,
        'repeat_interval': repeat_interval,
        'fee': fee,
        'conc_fee': conc_fee,
        'multi_day_fee': multi_day_fee,
        'multi_day_conc_fee': multi_day_conc_fee,
        'venue_id': venue.id,
    }

    event_date = EventDate(**data)

    if speakers:
        for s in speakers:
            event_date.speakers.append(s)

    dao_create_event_date(event_date)
    return event_date


def create_fee(event_type_id=None, fee=5, conc_fee=3, multi_day_fee=0, multi_day_conc_fee=0, valid_from=None):
    if not event_type_id:
        event_type = create_event_type(event_type='seminar')
        event_type_id = event_type.id

    data = {
        'event_type_id': event_type_id,
        'fee': fee,
        'conc_fee': conc_fee,
        'multi_day_fee': multi_day_fee,
        'multi_day_conc_fee': multi_day_conc_fee,
        'valid_from': valid_from
    }
    fee = Fee(**data)

    dao_create_fee(fee)
    return fee


def create_token_blacklist(sample_decoded_token):
    store_token(sample_decoded_token)
    return sample_decoded_token


def create_speaker(title='Mr', name='First Mid Last-name', parent_id=None):
    data = {
        'title': title,
        'name': name,
        'parent_id': parent_id
    }

    speaker = Speaker(**data)

    dao_create_speaker(speaker)
    return speaker


def create_venue(
    old_id='1',
    name='Head office',
    address='10 London Street, N1 1NN',
    directions='By bus: 100, 111, 123',
    default=True
):
    data = {
        'old_id': old_id,
        'name': name,
        'address': address,
        'directions': directions,
        'default': default
    }

    venue = Venue(**data)

    dao_create_venue(venue)
    return venue
