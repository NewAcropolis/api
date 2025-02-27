import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask import current_app, json, jsonify, url_for
from tests.conftest import create_authorization_header

from app.comms.encryption import encrypt
from app.models import Member

from tests.db import create_member


class WhenGettingMembers:

    def it_returns_all_members(self, client, db_session, sample_member):
        member = create_member(name='Sid Green', email='sid@example.com', active=False)

        response = client.get(
            url_for('members.get_members'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert len(response.json) == 2
        assert response.json[0] == jsonify(sample_member.serialize()).json
        assert response.json[1] == jsonify(member.serialize()).json

    def it_returns_member_by_email(self, client, db_session, sample_member):
        member = create_member(name='Sid Green', email='sid@example.com', active=True)
        unsubcode = encrypt(
            "{}={}".format(current_app.config['EMAIL_TOKENS']['member_id'], member.id),
            current_app.config['EMAIL_UNSUB_SALT']
        )
        _member_json = member.serialize()
        _member_json['unsubcode'] = unsubcode

        response = client.get(
            url_for('members.get_member_by_email', email=member.email),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.json == jsonify(_member_json).json

    def it_returns_404_nonmember_by_email(self, client, db_session, sample_member):
        response = client.get(
            url_for('members.get_member_by_email', email='unknown@email.com'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.json == {'message': 'No member found for unknown@email.com'}

    def it_gets_member_from_unsubcode(self, app, client, db_session, sample_member):
        unsubcode = encrypt(
            "{}={}".format(app.config['EMAIL_TOKENS']['member_id'], str(sample_member.id)),
            app.config['EMAIL_UNSUB_SALT']
        )

        response = client.get(
            url_for('members.get_member_from_unsubcode', unsubcode=unsubcode),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.json['id'] == str(sample_member.id)


class WhenPostingMembers:

    def it_subscribes_member(self, mocker, app, client, db_session, sample_marketing):
        mock_send_email = mocker.patch('app.routes.members.rest.send_email')
        mock_ga_event = mocker.patch('app.routes.members.rest.send_ga_event')
        data = {
            'name': 'Test member',
            'email': 'test@example.com',
            'marketing_id': sample_marketing.id
        }
        response = client.post(
            url_for('members.subscribe_member'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        members = Member.query.all()
        assert len(members) == 1
        assert members[0].name == data['name']
        assert members[0].email == data['email']
        assert members[0].active is True
        assert members[0].marketing_id == sample_marketing.id
        assert mock_ga_event.called
        assert mock_send_email.called
        assert mock_send_email.call_args[0][0] == data['email']
        assert mock_send_email.call_args[0][1] == 'New Acropolis subscription'
        assert 'Thank you {} for subscribing to New Acropolis events and magazines'.format(data['name']) \
            in mock_send_email.call_args[0][2]

    def it_doesnt_subscribes_member_with_matching_email(self, app, client, db_session, sample_member, sample_marketing):
        data = {
            'name': 'Test member',
            'email': sample_member.email,
            'marketing_id': sample_marketing.id
        }
        response = client.post(
            url_for('members.subscribe_member'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400
        members = Member.query.all()
        assert len(members) == 1

    def it_unsubscribes_member(self, mocker, app, client, db_session, sample_member):
        mock_send_email = mocker.patch('app.routes.members.rest.send_email')
        mock_ga_event = mocker.patch('app.routes.members.rest.send_ga_event')

        unsubcode = encrypt(
            "{}={}".format(app.config['EMAIL_TOKENS']['member_id'], str(sample_member.id)),
            app.config['EMAIL_UNSUB_SALT']
        )

        response = client.post(
            url_for('members.unsubscribe_member', unsubcode=unsubcode),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert not sample_member.active
        assert response.json == {'message': '{} unsubscribed'.format(sample_member.name)}
        assert mock_ga_event.called
        assert mock_send_email.called
        assert mock_send_email.call_args[0][0] == sample_member.email
        assert mock_send_email.call_args[0][1] == 'New Acropolis unsubscription'
        assert '{}, you have successfully unsubscribed from New Acropolis events and magazines'.format(
            sample_member.name) in mock_send_email.call_args[0][2]

    def it_updates_member(self, app, client, db_session, sample_member):
        unsubcode = encrypt(
            "{}={}".format(app.config['EMAIL_TOKENS']['member_id'], str(sample_member.id)),
            app.config['EMAIL_UNSUB_SALT']
        )
        old_name = sample_member.name

        data = {
            'name': 'New test member',
            'email': 'new_email@test.com',
            'active': True,
        }

        response = client.post(
            url_for('members.update_member', unsubcode=unsubcode),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        member = Member.query.one()
        assert response.json['message'] == '{} updated'.format(old_name)
        assert member.name == data['name']
        assert member.email == data['email']

    def it_imports_members(self, client, db_session, sample_marketing):
        data = [
            {
                "id": "1",
                "Name": "Test member",
                "EmailAdd": "test@example.com",
                "Active": "y",
                "CreationDate": "2019-08-01",
                "Marketing": "1",
                "IsMember": "n",
                "LastUpdated": "2019-08-10 10:00:00"
            },
            {
                "id": "2",
                "Name": "Test member 2",
                "EmailAdd": "test2@example.com",
                "Active": "y",
                "CreationDate": "2019-08-02",
                "Marketing": "1",
                "IsMember": "n",
                "LastUpdated": "2019-08-11 10:00:00"
            },
        ]
        response = client.post(
            url_for('members.import_members'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        members = Member.query.all()

        assert len(members) == 2
        assert members[0].old_id in [int(i['id']) for i in data]
        assert members[0].name in [n['Name'] for n in data]

    def it_doesnt_import_exising_members(self, client, db_session, sample_marketing, sample_member):
        data = [
            {
                "id": "1",
                "Name": "Test member",
                "EmailAdd": "test@example.com",
                "Active": "y",
                "CreationDate": "2019-08-01",
                "Marketing": "1",
                "IsMember": "n",
                "LastUpdated": "2019-08-10 10:00:00"
            },
            {
                "id": "2",
                "Name": "Test member 2",
                "EmailAdd": "test2@example.com",
                "Active": "y",
                "CreationDate": "2019-08-02",
                "Marketing": "1",
                "IsMember": "n",
                "LastUpdated": "2019-08-11 10:00:00"
            },
        ]
        response = client.post(
            url_for('members.import_members'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201
        assert response.json.get('errors') == ['member already exists: 1']

        members = Member.query.all()

        assert len(members) == 2

    def it_doesnt_import_members_with_invalid_marketing(self, client, db_session, sample_marketing, sample_member):
        data = [
            {
                "id": "2",
                "Name": "Test member 2",
                "EmailAdd": "test2@example.com",
                "Active": "y",
                "CreationDate": "2019-08-02",
                "Marketing": "2",
                "IsMember": "n",
                "LastUpdated": "2019-08-11 10:00:00"
            },
            {
                "id": "3",
                "Name": "Test member 3",
                "EmailAdd": "test3@example.com",
                "Active": "y",
                "CreationDate": "2019-08-02",
                "Marketing": "1",
                "IsMember": "n",
                "LastUpdated": "2019-08-11 10:00:00"
            },
        ]
        response = client.post(
            url_for('members.import_members'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201
        assert response.json.get('errors') == ['Cannot find marketing: 2']

        members = Member.query.all()

        assert len(members) == 2

    def it_doesnt_import_members_without_an_email_address(self, client, db_session, sample_marketing):
        data = [
            {
                "id": "2",
                "Name": "Test member 2",
                "EmailAdd": "test2@example.com",
                "Active": "y",
                "CreationDate": "2019-08-02",
                "Marketing": "1",
                "IsMember": "n",
                "LastUpdated": "2019-08-11 10:00:00"
            },
            {
                "id": "3",
                "Name": "Test member 3",
                "EmailAdd": "anon",
                "Active": "y",
                "CreationDate": "2019-08-02",
                "Marketing": "1",
                "IsMember": "n",
                "LastUpdated": "2019-08-11 10:00:00"
            },
        ]
        response = client.post(
            url_for('members.import_members'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        members = Member.query.all()

        assert len(members) == 1
