from freezegun import freeze_time

from app.dao.events_dao import (
    dao_create_event, dao_update_event, dao_get_events, dao_get_future_events
)
from app.models import Event

from tests.db import create_event, create_event_date


class WhenUsingEventsDAO(object):

    def it_creates_an_event(self, db, db_session):
        event = create_event()

        assert Event.query.count() == 1
        event_from_db = Event.query.first()
        assert event == event_from_db

    def it_creates_an_event_with_event_dates(self, db, db_session):
        event_date = create_event_date()
        event = create_event(event_dates=[event_date])

        assert Event.query.count() == 1
        event_from_db = Event.query.first()
        assert event == event_from_db
        assert event_from_db.event_dates[0] == event_date

    def it_updates_an_event_dao(self, db, db_session, sample_event):
        dao_update_event(sample_event.id, title='new title')

        event_from_db = Event.query.filter(Event.id == sample_event.id).first()

        assert sample_event.title == event_from_db.title

    def it_gets_all_events(self, db, db_session, sample_event, sample_event_type):
        events = [create_event(title='test title 2', event_type_id=sample_event_type.id), sample_event]
        events_from_db = dao_get_events()

        assert Event.query.count() == 2
        assert set(events) == set(events_from_db)

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
