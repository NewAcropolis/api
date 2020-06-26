import json
import pytest
import uuid

from flask import json, url_for
from tests.conftest import create_authorization_header


class WhenPostingEmailProvider(object):

    def it_creates_an_email_provider(self, client, db_session):
        data_struct = {
            "to": "<<to>>",
            "to": "<<to>>",
            "subject": "<<subject>>",
            "message": "<<message>>"
        }

        data = {
            "name": "Test provider",
            "daily_limit": 100,
            "api_key": "api-key",
            "api_url": "http://api-url.com",
            "data_struct": json.dumps(data_struct),
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
            assert data[key] == json_resp[key]

    def it_updates_an_email_provider_on_valid_post_data(self, client, db_session, sample_email_provider):
        data = {
            "daily_limit": 200,
            "api_key": "new-api-key",
            "api_url": "http://new-api-url.com",
            "pos": 1,
        }
        response = client.post(
            url_for('email_provider.update_email_provider', email_provider_id=sample_email_provider.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            assert data[key] == json_resp[key]
