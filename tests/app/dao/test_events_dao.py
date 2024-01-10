from freezegun import freeze_time

from app.dao.event_dates_dao import dao_get_event_date_by_id

from app.dao.events_dao import (
    dao_create_event,
    dao_delete_event,
    dao_update_event,
    dao_get_events,
    dao_get_event_by_id,
    dao_get_events_in_year,
    dao_get_future_events,
    dao_get_limited_events,
    dao_get_past_year_events,
    dao_get_existing_event_at_venue
)
from app.models import Event, EventDate, RejectReason

from tests.db import create_event, create_event_date, create_speaker


class WhenUsingEventsDAO(object):

    def it_creates_an_event(self, db, db_session):
        event = create_event()

        assert Event.query.count() == 1
        event_from_db = Event.query.first()
        assert event == event_from_db

    def it_deletes_an_event(self, db, db_session):
        event = create_event()

        assert Event.query.count() == 1

        dao_delete_event(event.id)

        assert Event.query.count() == 0

    def it_creates_an_event_with_event_dates(self, db, db_session):
        event_date = create_event_date()
        event = create_event(event_dates=[event_date])

        assert Event.query.count() == 1
        event_from_db = Event.query.first()
        assert event == event_from_db
        assert event_from_db.event_dates[0] == event_date

    def it_deletes_an_event_with_event_dates(self, db, db_session):
        event_date = create_event_date()
        event = create_event(event_dates=[event_date])

        assert Event.query.count() == 1

        dao_delete_event(event.id)

        assert Event.query.count() == 0

    def it_updates_an_event_dao(self, db, db_session, sample_event):
        dao_update_event(sample_event.id, title='new title')

        event_from_db = Event.query.filter(Event.id == sample_event.id).first()

        assert sample_event.title == event_from_db.title

    def it_updates_an_event_dao_with_new_event_date(self, db, db_session, sample_event):
        speaker = create_speaker(name='John Brown')
        event_date = create_event_date(event_datetime='2018-01-20T19:00:00', speakers=[speaker])

        dao_update_event(sample_event.id, event_dates=[event_date])

        event_from_db = Event.query.filter(Event.id == sample_event.id).first()

        assert sample_event.event_dates[0] == event_from_db.event_dates[0]

        event_date2 = create_event_date(event_datetime='2018-02-20T19:00:00', speakers=[speaker])

        dao_update_event(sample_event.id, event_dates=[event_date2])

        event_dates = EventDate.query.all()

        assert len(event_dates) == 1

    def it_updates_an_event_dao_with_new_speaker(self, db, db_session):
        speaker = create_speaker(name='John Brown')
        event_date = create_event_date(event_datetime='2018-01-20T19:00:00', speakers=[speaker])
        event = create_event(event_dates=[event_date])

        speaker2 = create_speaker(name='Jim Blue')

        db_event_date = dao_get_event_date_by_id(event_date.id)

        db_event_date.speakers = [speaker, speaker2]

        dao_update_event(event.id, event_dates=[db_event_date])

        event_from_db = Event.query.filter(Event.id == event.id).first()

        assert event.event_dates[0] == event_from_db.event_dates[0]

        event_dates = EventDate.query.all()

        assert len(event_dates) == 1

    def it_gets_all_events(self, db, db_session, sample_event, sample_event_type):
        events = [create_event(title='test title 2', event_type_id=sample_event_type.id), sample_event]
        events_from_db = dao_get_events()

        assert Event.query.count() == 2
        assert set(events) == set(events_from_db)

    def it_gets_event_by_id(self, db, db_session, sample_event, sample_event_type):
        create_event(title='test title 2', event_type_id=sample_event_type.id)
        event_from_db = dao_get_event_by_id(sample_event.id)

        assert Event.query.count() == 2
        assert event_from_db == sample_event

    def it_gets_event_by_id_with_reject_reason(self, db_session, sample_event_type, sample_reject_reason):
        event_from_db = dao_get_event_by_id(sample_reject_reason.event_id)

        assert Event.query.count() == 1
        assert event_from_db.reject_reasons == [sample_reject_reason]

    @freeze_time("2018-01-10T19:00:00")
    def it_gets_all_future_events(self, db, db_session, sample_event_with_dates, sample_event_type):
        event = create_event(
            title='future event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2018-01-20T19:00:00')]
        )
        events_from_db = dao_get_future_events()

        assert Event.query.count() == 2
        assert len(events_from_db) == 1
        assert events_from_db[0] == event

    @freeze_time("2018-01-10T19:00:00")
    def it_gets_past_year_events(self, db, db_session, sample_event_with_dates, sample_event_type):
        create_event(
            title='way past last year event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2016-01-01T19:00:00')]
        )
        create_event(
            title='future event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2018-01-20T19:00:00')]
        )
        events_from_db = dao_get_past_year_events()

        assert Event.query.count() == 3
        assert len(events_from_db) == 1
        assert events_from_db[0] == sample_event_with_dates

    def it_gets_events_in_year(self, db, db_session, sample_event_with_dates, sample_event_type):
        event_2 = create_event(
            title='2018 event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2018-12-31T23:59:00')]
        )
        create_event(
            title='2017 event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2017-12-31T23:59:59')]
        )
        create_event(
            title='2019 event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2019-01-01T00:00:01')]
        )
        events_from_db = dao_get_events_in_year(2018)

        assert len(events_from_db) == 2
        assert events_from_db[0] == sample_event_with_dates
        assert events_from_db[1] == event_2

    def it_gets_limited_events(self, db, db_session, sample_event_with_dates, sample_event_type):
        event_2 = create_event(
            title='2018 event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2018-12-31T23:59:00')]
        )
        create_event(
            title='beyond limit',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2017-12-31T23:59:59')]
        )
        events_from_db = dao_get_limited_events(2)

        assert len(events_from_db) == 2
        assert events_from_db[0] == event_2
        assert events_from_db[1] == sample_event_with_dates

    def it_gets_existing_event_at_venue(self, db_session, sample_event_with_dates, sample_event, sample_event_type):
        create_event(
            title='another event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2017-12-31T23:59:59')]
        )

        duplicate_events = dao_get_existing_event_at_venue(
            [
                str(sample_event_with_dates.event_dates[0].event_datetime),
                str(sample_event_with_dates.event_dates[1].event_datetime)
            ],
            sample_event_with_dates.venue_id)

        assert len(duplicate_events) == 1
