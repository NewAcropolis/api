import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

import pytest
from flask import json, url_for
from tests.conftest import create_authorization_header
from app.models import User, USER_ADMIN
from app.dao.users_dao import dao_get_admin_users
from tests.conftest import TEST_ADMIN_USER_CONFIG
from tests.db import create_user


class WhenGettingUsers(object):

    def it_returns_all_users(self, client, sample_user, db_session):
        response = client.get(
            url_for('users.get_users'),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        data = json.loads(response.get_data(as_text=True))

        assert len(data) == 1


class WhenCheckingIfAdminUser:

    def it_returns_true_for_admin_user(self, app, client, sample_admin_user, db_session):
        response = client.get(
            url_for('user.is_admin', email=TEST_ADMIN_USER_CONFIG),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        data = json.loads(response.get_data(as_text=True))

        assert data['is_admin']
        assert data['email'] == TEST_ADMIN_USER_CONFIG

    def it_returns_true_for_admin_user_created_on_web_app(self, client, sample_admin_user, db_session):
        response = client.get(
            url_for('user.is_admin', email=sample_admin_user.email),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        data = json.loads(response.get_data(as_text=True))

        assert data['is_admin']
        assert data['email'] == sample_admin_user.email

    def it_returns_false_if_not_admin(self, client, sample_user, db_session):
        response = client.get(
            url_for('user.is_admin', email=sample_user.email),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        data = json.loads(response.get_data(as_text=True))

        assert not data['is_admin']
        assert data['email'] == sample_user.email


class WhenGettingUserByEmail(object):

    def it_returns_correct_user(self, client, sample_user, db_session):
        response = client.get(
            url_for('user.get_user_by_email', email=sample_user.email),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['id'] == str(sample_user.id)

    def it_raises_404_if_user_not_exist(self, client, db_session):
        response = client.get(
            url_for('user.get_user_by_email', email='other@example.com'),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 404

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp == {'result': 'error', 'message': 'other@example.com not found'}


class WhenPostingUser(object):

    def it_creates_admin_user_if_email_is_admin_in_env_var(self, mocker, client, db_session):
        data = {'email': 'admin-config@example.com', 'name': 'Admin User', 'access_area': ',email,'}
        response = client.post(
            url_for('user.create_user'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['access_area'] == USER_ADMIN
        assert dao_get_admin_users()[0].email == data['email']

    def it_does_not_create_admin_user_if_email_is_not_admin_in_env_var(self, mocker, client, db_session):
        data = {'email': 'gary@example.com', 'name': 'Gary Blue', 'access_area': ',email,'}
        response = client.post(
            url_for('user.create_user'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            assert data[key] == json_resp[key]
        assert json_resp['access_area'] == ',email,'

    @pytest.mark.parametrize('data', [
        {'email': 'sarah@example.com', 'name': 'Sarah Black', 'access_area': ',email,'},
        {'email': 'diane@example.com', 'access_area': ',email,'},
        {'email': 'diane@example.com'}
    ])
    def it_creates_a_user_on_valid_post_data(self, mocker, client, data, db_session, sample_admin_user):
        response = client.post(
            url_for('user.create_user'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            assert data[key] == json_resp[key]

        assert json_resp['active']

    def it_raises_an_error_on_invalid_access_area(self, mocker, client, db_session, sample_admin_user):
        data = {'email': 'sarah@example.com', 'name': 'Sarah Black', 'access_area': ',invalid,'}
        response = client.post(
            url_for('user.create_user'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        json_resp = json.loads(response.get_data(as_text=True))

        assert response.status_code == 400
        assert json_resp['message'] == 'invalid not supported access area'

    @pytest.mark.parametrize('data,error_msg', [
        ({'name': 'Sophia Grey', 'access_area': ',email,'}, ['email is a required property']),
    ])
    def it_returns_400_on_invalid_post_user_data(self, mocker, client, data, error_msg, db_session):
        response = client.post(
            url_for('user.create_user'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert all([e['error'] == "ValidationError" for e in json_resp['errors']])
        for i, err in enumerate(json_resp['errors']):
            assert json_resp['errors'][i]['message'] == error_msg[i]

    def it_updates_a_user_on_valid_post_data(self, mocker, client, sample_user, db_session):
        data = {'email': 'sarah@example.com', 'name': 'Sarah Black', 'access_area': ',email,'}
        response = client.post(
            url_for('user.update_user', user_id=str(sample_user.id)),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            assert data[key] == json_resp[key]

    def it_doesnt_create_user_with_same_email(self, mocker, client, db_session, sample_user):
        data = {'email': sample_user.email, 'name': 'Test user', 'access_area': ',email,'}

        response = client.post(
            url_for('user.create_user'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['result'] == 'error'
        assert json_resp['message'] == 'User email already exists'

        users = User.query.all()
        assert len(users) == 1

    def it_doesnt_create_user_with_wrong_email_domain(self, mocker, client, db_session, sample_user):
        data = {'email': 'other@wrong.com', 'name': 'Test user', 'access_area': ',email,'}

        response = client.post(
            url_for('user.create_user'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['result'] == 'error'
        assert json_resp['message'] == 'other@wrong.com not in correct domain'

        users = User.query.all()
        assert len(users) == 1

    def it_returns_500_on_user_unknown_error(self, client, db_session):
        from app.routes.users.rest import handle_integrity_error

        class MockIntegrityError:
            def __str__(self):
                return 'other_key error'

        response, status = handle_integrity_error(MockIntegrityError())

        json_resp = json.loads(response.get_data(as_text=True))

        assert status == 500
        assert json_resp['message'] == 'Internal server error'
