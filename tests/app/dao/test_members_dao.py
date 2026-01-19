from sqlalchemy.exc import IntegrityError
import pytest

from app.dao.emails_dao import dao_create_email_to_member
from app.dao.members_dao import (
    dao_update_member,
    dao_get_member_by_id,
    dao_get_members_not_sent_to,
    dao_get_member_by_email,
    dao_get_new_member_count,
    dao_get_unsubscribed_member_count
)
from app.models import EmailToMember, Member
from freezegun import freeze_time

from tests.db import create_member


class WhenUsingMembersDAO(object):

    def it_creates_an_member(self, db_session):
        member = create_member()
        assert Member.query.count() == 1

        member_from_db = Member.query.filter(Member.id == member.id).first()

        assert member == member_from_db

    def it_updates_a_member_dao(self, db, db_session, sample_member):
        dao_update_member(sample_member.id, email='new@example.com')

        member_from_db = Member.query.filter(Member.id == sample_member.id).first()

        assert member_from_db.email == 'new@example.com'

    def it_gets_an_member_by_id(self, db, db_session, sample_member):
        member = create_member(name='Sid Grey', email='sid@example.com')

        fetched_member = dao_get_member_by_id(member.id)
        assert fetched_member == member

    def it_gets_an_member_by_old_id(self, db, db_session):
        member = create_member(name='Sid Grey', email='sid@example.com', old_id='1')

        fetched_member = dao_get_member_by_id(member.old_id)
        assert fetched_member == member

    def it_doesnt_create_members_with_same_email(self, db_session, sample_member):
        with pytest.raises(expected_exception=IntegrityError):
            create_member(name='Sid Grey', email=sample_member.email)

        members = Member.query.all()
        assert len(members) == 1

    def it_doesnt_update_members_with_same_email(self, db_session, sample_member):
        member = create_member(email='another@example.com')
        with pytest.raises(expected_exception=IntegrityError):
            dao_update_member(str(member.id), email=sample_member.email)

        members = Member.query.all()
        assert len(members) == 2
        assert members[0].email == sample_member.email
        assert members[1].email == member.email

    def it_gets_only_members_not_sent_to(self, db_session, sample_member, sample_email):
        member = create_member(email='another@example.com')
        create_member(email='inactive@example.com', active=False)
        email_to_member = EmailToMember(
            email_id=sample_email.id,
            member_id=sample_member.id,
            created_at='2019-08-01 12:00:00'
        )
        dao_create_email_to_member(email_to_member)

        unsent_members = dao_get_members_not_sent_to(sample_email.id)

        member_id, email = unsent_members[0]

        assert len(unsent_members) == 1
        assert str(member_id) == str(member.id)
        assert email == member.email

    def it_gets_member_by_email(self, db_session):
        member = create_member(email='Test@example.com')
        member_found = dao_get_member_by_email('test@example.com')

        assert member_found
        assert member_found.email == member.email

    def it_gets_new_members_count(self, db_session):
        members = [
            create_member(email='Test@example.com', created_at="2025-12-01T00:00:00"),
            create_member(email='Test2@example.com', created_at="2025-12-31T23:00:00")
        ]
        create_member(email='Test3@example.com', created_at="2025-11-30T23:00:00")
        create_member(email='Test4@example.com', created_at="2026-01-31T23:00:00")

        new_members_count = dao_get_new_member_count(12, 2025)

        assert new_members_count == len(members)

    def it_gets_new_members_count_range(self, db_session):
        members = [
            create_member(email='Test@example.com', created_at="2025-12-01T00:00:00"),
            create_member(email='Test2@example.com', created_at="2025-12-31T23:00:00"),
            create_member(email='Test2a@example.com', created_at="2026-01-31T23:00:00")
        ]
        create_member(email='Test3@example.com', created_at="2025-11-30T23:00:00")
        create_member(email='Test4@example.com', created_at="2026-03-31T23:00:00")

        new_members_count = dao_get_new_member_count(12, 2025, 2, 2026)

        assert new_members_count == len(members)

    def it_gets_unsub_members_count(self, db_session):
        members = [
            create_member(email='Test@example.com', created_at="2025-12-01T00:00:00"),
            create_member(email='Test2@example.com', created_at="2025-12-31T23:00:00"),
            create_member(email='Test3@example.com', created_at="2025-11-30T23:00:00")
        ]

        Member.query.filter_by(id=members[0].id).update(
            {
                "active": False,
                "last_updated": "2025-12-31T23:00:00"
            }
        )
        Member.query.filter_by(id=members[2].id).update(
            {
                "active": False,
                "last_updated": "2025-11-30T23:00:00"
            }
        )

        unsub_count = dao_get_unsubscribed_member_count(12, 2025)

        assert unsub_count == 1

    def it_gets_unsub_members_count_for_month_range(self, db_session):
        members = [
            create_member(email='Test@example.com', created_at="2025-12-01T00:00:00"),
            create_member(email='Test2@example.com', created_at="2025-12-31T23:00:00"),
            create_member(email='Test3@example.com', created_at="2025-11-30T23:00:00"),
            create_member(email='Test4@example.com', created_at="2026-01-10T23:00:00")
        ]

        Member.query.filter_by(id=members[0].id).update(
            {
                "active": False,
                "last_updated": "2025-12-31T23:00:00"
            }
        )
        Member.query.filter_by(id=members[2].id).update(
            {
                "active": False,
                "last_updated": "2025-11-30T23:00:00"
            }
        )

        unsub_count = dao_get_unsubscribed_member_count(11, 2025, 12, 2025)

        assert unsub_count == 2
