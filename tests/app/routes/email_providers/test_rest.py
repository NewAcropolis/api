import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

import json
import pytest
import uuid

from flask import json, url_for
from tests.conftest import create_authorization_header
from tests.db import create_email_provider


class WhenGettingEmailProviders:
    def it_gets_email_providers_in_order(self, client, db, db_session, sample_email_provider):
        next_email_provider = create_email_provider(
            name='Next email provider', pos=2,
            smtp_server='http://smtp.test', smtp_user='user', smtp_password='password')

        response = client.get(
            url_for('email_provider.get_email_providers'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200
        assert len(response.json) == 2
        assert response.json[0]['id'] == str(sample_email_provider.id)
        assert 'api_key' not in response.json[0]
        assert response.json[0]['shortened_api_key'] == sample_email_provider.api_key[-10:]
        assert response.json[1]['id'] == str(next_email_provider.id)
        assert 'api_key' not in response.json[1]
        assert response.json[1]['shortened_api_key'] == next_email_provider.api_key[-10:]
        assert response.json[1]['shortened_smtp_password'] == next_email_provider.smtp_password[-5:]


class WhenPostingEmailProvider:

    def it_creates_an_email_provider(self, client, db_session):
        data_map = {
            "to": "to",
            "from": "from",
            "subject": "subject",
            "message": "message"
        }

        data = {
            "name": "Test provider",
            "daily_limit": 100,
            "api_key": "api-key",
            "api_url": "http://api-url.com",
            "data_map": json.dumps(data_map),
            "pos": 0,
        }
        response = client.post(
            url_for('email_provider.create_email_provider'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            if key == 'data_map':
                assert json.loads(data[key]) == json_resp[key]
            else:
                assert data[key] == json_resp[key]

    def it_updates_an_email_provider_on_valid_post_data(self, client, db_session, sample_email_provider):
        data_map = {
            "to": "to",
            "from": "from",
            "subject": "subject",
            "message": "text"
        }

        data = {
            "daily_limit": 200,
            "api_key": "new-api-key",
            "api_url": "http://new-api-url.com",
            "pos": 1,
            "data_map": json.dumps(data_map),
        }
        response = client.post(
            url_for('email_provider.update_email_provider', email_provider_id=sample_email_provider.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            if key == 'data_map':
                assert json.loads(data[key]) == json_resp[key]
            else:
                assert data[key] == json_resp[key]
