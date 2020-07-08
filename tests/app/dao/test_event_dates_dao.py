from datetime import datetime

from app.dao.event_dates_dao import (
    dao_create_event_date,
    dao_delete_event_date,
    dao_update_event_date,
    dao_get_event_dates,
    dao_get_event_date_by_id,
    dao_get_event_dates_by_event_id,
    dao_get_event_date_on_date
)
from app.models import EventDate

from tests.db import create_event_date, create_event, create_fee


class WhenUsingEventDatesDAO(object):

    def it_creates_an_event_date(self, db, db_session):
        event_date = create_event_date()

        assert EventDate.query.count() == 1
        event_date_from_db = EventDate.query.first()
        assert event_date == event_date_from_db

    def it_deletes_an_event_date(self, db, db_session):
        event_date = create_event_date()

        assert EventDate.query.count() == 1

        dao_delete_event_date(event_date.id)

        assert EventDate.query.count() == 0

    def it_creates_an_event_date_with_speaker(self, db, db_session, sample_speaker):
        create_event_date(speakers=[sample_speaker])

        assert EventDate.query.count() == 1
        event_date_from_db = EventDate.query.first()
        assert event_date_from_db.speakers[0] == sample_speaker

    def it_deletes_an_event_date_with_speaker(self, db, db_session, sample_speaker):
        event_date = create_event_date(speakers=[sample_speaker])

        assert EventDate.query.count() == 1

        dao_delete_event_date(event_date.id)

    def it_updates_an_event_date_dao(self, db, db_session, sample_event_date):
        event_from_db = EventDate.query.filter(EventDate.id == sample_event_date.id).first()

        assert event_from_db.event_datetime == datetime(2018, 1, 1, 19, 0)

        dao_update_event_date(sample_event_date.id, event_datetime='2018-03-19 19:30')

        event_from_db = EventDate.query.filter(EventDate.id == sample_event_date.id).first()

        assert event_from_db.event_datetime == datetime(2018, 3, 19, 19, 30)

    def it_gets_all_event_dates(self, db_session, sample_event_date):
        create_event_date(event_datetime='2018-03-19 19:30', event_id=sample_event_date.event_id)

        event_dates = dao_get_event_dates()
        event_dates_json = [e.serialize() for e in event_dates]

        assert EventDate.query.count() == 2

        event_dates_from_db = EventDate.query.all()
        event_dates_from_db_json = [e.serialize() for e in event_dates_from_db]

        assert sorted(event_dates_json, key=lambda e: e['id']) == \
            sorted(event_dates_from_db_json, key=lambda e: e['id'])

    def it_gets_an_event_date(self, db, db_session, sample_event_date):
        event_date = dao_get_event_date_by_id(str(sample_event_date.id))

        assert event_date.id == sample_event_date.id

    def it_gets_event_dates_by_event_id(self, db_session, sample_event_date, sample_event_type):
        event = create_event(event_type_id=sample_event_type.id)
        create_event_date(event_id=event.id)

        assert len(EventDate.query.all()) == 2

        event_dates = dao_get_event_dates_by_event_id(sample_event_date.event_id)
        assert len(event_dates) == 1

    def it_gets_event_date_on_date(self, db_session, sample_event_with_dates):
        target_date = sample_event_with_dates.event_dates[0].event_datetime.strftime('%Y-%m-%d')
        event_date = dao_get_event_date_on_date(target_date)
        assert event_date.event_id == sample_event_with_dates.id
