
from app.dao.users_dao import (
    dao_get_admin_users,
    dao_update_user,
    dao_get_users,
    dao_get_user_by_id,
    dao_get_user_by_email
)
from app.models import User

from tests.db import create_user


class WhenUsingUsersDAO(object):

    def it_creates_a_user(self, db):
        user = create_user()
        assert user.query.count() == 1

        user_from_db = user.query.filter(user.id == user.id).first()

        assert user == user_from_db

    def it_updates_a_user_dao(self, db, db_session, sample_user):
        dao_update_user(sample_user.id, name='Gary Green')

        user_from_db = User.query.filter(User.id == sample_user.id).first()

        assert sample_user.name == user_from_db.name

    def it_gets_all_users_in_last_name_alphabetical_order(self, db, db_session, sample_user):
        users = [
            create_user(email='bob@example.com', name='Bob Blue'),
            create_user(email='sid@example.com', name='Sid Green'),
            sample_user
        ]

        users_from_db = dao_get_users()
        assert users == users_from_db

    def it_gets_a_user_by_id(self, db, db_session, sample_user):
        user = create_user(email='sam@example.com', name='Sam Black')

        fetched_user = dao_get_user_by_id(user.id)
        assert fetched_user == user

    def it_gets_a_user_by_email(self, db, db_session, sample_user):
        user = create_user(email='sam@example.com', name='Sam Black')

        fetched_user = dao_get_user_by_email(user.email)
        assert fetched_user == user

    def it_gets_admin_users(self, db, db_session, sample_user):
        user = create_user(email='admin@example.com', name='Sam Black', access_area='admin')

        admin_users = dao_get_admin_users()

        assert len(admin_users) == 1
        assert admin_users == [user]
        assert admin_users[0].is_admin()

    def it_does_not_get_admin_user_if_no_admin(self, db, db_session, sample_user):
        admin_user = dao_get_admin_users()

        assert not admin_user
