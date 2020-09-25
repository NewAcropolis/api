import json
import pytest
import uuid

from flask import json, url_for
from tests.conftest import create_authorization_header
from tests.db import create_email_provider


class WhenPostingEmailProvider(object):

    def it_gets_current_email_provider(self, client, db_session, sample_email_provider):
        create_email_provider(name='Next email provider', pos=2)

        response = client.get(
            url_for('email_provider.get_email_provider'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200
        assert response.json['id'] == str(sample_email_provider.id)
        assert response.json['shortened_api_key'] == sample_email_provider.api_key[-10:]

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
