
from app.dao.venues_dao import (
    dao_update_venue, dao_get_venues, dao_get_venue_by_id, dao_get_venue_by_old_id
)
from app.models import Venue

from tests.db import create_venue


class WhenUsingvenuesDAO(object):

    def it_creates_a_venue(self, db_session):
        venue = create_venue()
        assert Venue.query.count() == 1

        venue_from_db = Venue.query.filter(Venue.id == venue.id).first()

        assert venue == venue_from_db
        assert venue.default

    def it_creates_a_venue_a_default_if_none_set(self, db_session):
        venue = create_venue(default=False)
        assert Venue.query.count() == 1

        venue_from_db = Venue.query.filter(Venue.id == venue.id).first()

        assert venue == venue_from_db
        assert venue.default

    def it_updates_a_venue(self, db, db_session, sample_venue):
        dao_update_venue(sample_venue.id, address="10 New Venue")

        venue_from_db = Venue.query.filter(Venue.id == sample_venue.id).first()

        assert sample_venue.address == venue_from_db.address

    def it_updates_one_venue_to_default(self, db, db_session, sample_venue):
        assert sample_venue.default

        venue = create_venue()
        dao_update_venue(venue.id, default=True)

        assert not sample_venue.default
        assert venue.default

    def it_gets_all_venues(self, db, db_session, sample_venue):
        venues = [create_venue(address="20 New Venue"), sample_venue]

        venues_from_db = dao_get_venues()
        assert Venue.query.count() == 2
        assert set(venues) == set(venues_from_db)

    def it_gets_a_venue_by_id(self, db, db_session, sample_venue):
        venue = create_venue(directions="By Train: 5 mins walk from Highbury & Islington")

        fetched_venue = dao_get_venue_by_id(venue.id)
        assert fetched_venue == venue

    def it_gets_a_venue_by_old_id(self, db, db_session, sample_venue):
        create_venue(directions="By Train: 5 mins walk from Highbury & Islington")

        fetched_venue = dao_get_venue_by_old_id(sample_venue.old_id)
        assert fetched_venue == sample_venue
