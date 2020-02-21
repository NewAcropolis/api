from datetime import datetime, timedelta
import pytest
from freezegun import freeze_time
from sqlalchemy.exc import IntegrityError

from app.dao.emails_dao import (
    dao_add_member_sent_to_email,
    dao_get_emails_for_year_starting_on,
    dao_get_email_by_id,
    dao_get_future_emails,
    dao_get_latest_emails,
    dao_update_email,
    _get_nearest_bi_monthly_send_date
)
from app.errors import InvalidRequest
from app.models import Email, EmailToMember, ANON_REMINDER, ANNOUNCEMENT, MAGAZINE

from tests.db import create_email, create_magazine, create_member


class WhenUsingEmailsDAO(object):

    def it_creates_an_email(self, db_session):
        email = create_email()
        assert Email.query.count() == 1

        email_from_db = Email.query.filter(Email.id == email.id).first()

        assert email == email_from_db

    @freeze_time("2019-12-29T23:00:00")
    def it_creates_a_magazine_email(self, db_session):
        magazine = create_magazine()
        email = create_email(magazine_id=magazine.id, email_type=MAGAZINE, old_id=None)
        assert Email.query.count() == 1

        email_from_db = Email.query.filter(Email.id == email.id).first()

        assert email == email_from_db
        assert email_from_db.magazine_id == magazine.id

    def it_doesnt_create_a_magazine_email_if_no_match(self, db_session, sample_uuid):
        with pytest.raises(expected_exception=InvalidRequest):
            create_email(magazine_id=sample_uuid, email_type=MAGAZINE, old_id=None)
        assert Email.query.count() == 0

    def it_doesnt_create_a_magazine_email_if_no_magazine_id(self, db_session):
        create_email(email_type=MAGAZINE, old_id=None)
        assert Email.query.count() == 0

    def it_creates_an_event_email(self, db_session, sample_event_with_dates):
        email = create_email(event_id=sample_event_with_dates.id, old_event_id=None)
        assert Email.query.count() == 1

        email_from_db = Email.query.filter(Email.id == email.id).first()

        assert email == email_from_db
        assert email_from_db.send_starts_at == \
            datetime.strptime(sample_event_with_dates.get_first_event_date(), "%Y-%m-%d") - timedelta(weeks=2)

    def it_updates_an_email_dao(self, db, db_session, sample_email):
        dao_update_email(sample_email.id, send_starts_at='2019-06-05', extra_txt='test update')

        email_from_db = Email.query.filter(Email.id == sample_email.id).first()

        assert email_from_db.extra_txt == 'test update'

    def it_updates_an_email_with_members_sent_to_dao(self, db, db_session, sample_email, sample_member):
        members = [sample_member]
        dao_update_email(sample_email.id, members_sent_to=members)

        email_from_db = Email.query.filter(Email.id == sample_email.id).first()

        assert email_from_db.members_sent_to == members

    def it_adds_a_member_sent_to_email_for_first_member(self, db, db_session, sample_email, sample_member):
        dao_add_member_sent_to_email(sample_email.id, sample_member.id, created_at='2019-08-1 12:00:00')
        email_from_db = Email.query.filter(Email.id == sample_email.id).first()

        assert email_from_db.members_sent_to == [sample_member]
        email_to_member = EmailToMember.query.filter_by(email_id=sample_email.id, member_id=sample_member.id).first()
        assert str(email_to_member.created_at) == '2019-08-01 12:00:00'

    def it_adds_a_member_sent_to_email(self, db, db_session, sample_email, sample_member):
        members = [sample_member]
        dao_update_email(sample_email.id, members_sent_to=members)

        member = create_member(name='New member', email='new_member@example.com')

        dao_add_member_sent_to_email(sample_email.id, member.id)
        email_from_db = Email.query.filter(Email.id == sample_email.id).first()

        assert email_from_db.members_sent_to == [sample_member, member]

    def it_does_not_add_an_existing_member_sent_to_email(self, db, db_session, sample_email, sample_member):
        members = [sample_member]
        dao_update_email(sample_email.id, members_sent_to=members)

        with pytest.raises(expected_exception=IntegrityError):
            dao_add_member_sent_to_email(sample_email.id, sample_member.id)

        email_from_db = Email.query.filter(Email.id == sample_email.id).first()

        assert email_from_db.members_sent_to == [sample_member]

    @freeze_time("2019-06-10T10:00:00")
    def it_gets_emails_from_starting_date_from_last_year(self, db, db_session, sample_email):
        emails = [create_email(details='more details', created_at='2019-01-01'), sample_email]

        emails_from_db = dao_get_emails_for_year_starting_on()
        assert Email.query.count() == 2
        assert set(emails) == set(emails_from_db)

    @freeze_time("2019-06-10T10:00:00")
    def it_gets_emails_from_starting_date_from_specified_date(self, db, db_session):
        emails = [
            create_email(details='more details', created_at='2019-02-01'),
            create_email(details='more details', created_at='2018-02-01')
        ]

        emails_from_db = dao_get_emails_for_year_starting_on('2018-01-01')
        assert len(emails_from_db) == 1
        assert emails[1] == emails_from_db[0]

    def it_gets_an_email_by_id(self, db, db_session, sample_email):
        email = create_email(details='new event details')

        fetched_email = dao_get_email_by_id(email.id)
        assert fetched_email == email

    @freeze_time("2019-07-10T10:00:00")
    def it_gets_future_emails(self, db, db_session):
        active_email = create_email(created_at='2019-07-01 11:00', send_starts_at='2019-07-10', expires='2019-07-20')
        active_email_2 = create_email(created_at='2019-07-01 11:00', send_starts_at='2019-07-01', expires='2019-07-12')
        active_email_3 = create_email(created_at='2019-07-01 11:00', send_starts_at='2019-07-11', expires='2019-07-18')
        # these emails below are not active
        create_email(created_at='2019-07-01 11:00', send_starts_at='2019-07-01', expires='2019-07-09')

        emails_from_db = dao_get_future_emails()
        assert len(emails_from_db) == 3
        assert emails_from_db[0] == active_email
        assert emails_from_db[1] == active_email_2
        assert emails_from_db[2] == active_email_3

    def it_gets_latest_announcement_event_magazine_emails(self, db_session, sample_magazine):
        event_email = create_email()
        magazine_email = create_email(email_type=MAGAZINE, magazine_id=sample_magazine.id)
        announcement_email = create_email(email_type=ANNOUNCEMENT)
        anon_reminder_email = create_email(email_type=ANON_REMINDER)

        emails = dao_get_latest_emails()

        assert len(emails) == 3
        assert set([event_email, magazine_email, announcement_email]) == set(emails)
        assert anon_reminder_email not in emails

    def it_gets_latest_magazine_email_only(self, db_session, sample_magazine):
        later_magazine = create_magazine(title='ignored magazine')
        event_email = create_email()
        create_email(email_type=MAGAZINE, magazine_id=sample_magazine.id)
        later_magazine_email = create_email(email_type=MAGAZINE, magazine_id=later_magazine.id)

        emails = dao_get_latest_emails()

        assert len(emails) == 2
        assert set([event_email, later_magazine_email]) == set(emails)


class WhenGettingNearestBimonthlyDate:

    @freeze_time("2019-12-27T10:00:00")
    def it_gets_the_nearest_bimonthly_send_date(self):
        date = _get_nearest_bi_monthly_send_date()
        assert str(date) == '2020-01-01 00:00:00'

    @freeze_time("2020-01-05T10:00:00")
    def it_gets_the_nearest_bimonthly_send_date_after_day_passed(self):
        date = _get_nearest_bi_monthly_send_date()
        assert str(date) == '2020-01-01 00:00:00'

    @freeze_time("2019-12-05T10:00:00")
    def it_gets_the_nearest_bimonthly_send_date_before(self):
        date = _get_nearest_bi_monthly_send_date()
        assert str(date) == '2020-01-01 00:00:00'

    @freeze_time("2020-02-01T10:00:00")
    def it_gets_the_nearest_bimonthly_send_date_month_before(self):
        date = _get_nearest_bi_monthly_send_date()
        assert str(date) == '2020-03-01 00:00:00'
