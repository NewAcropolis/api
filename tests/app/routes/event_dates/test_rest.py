import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

import pytest

from flask import json, url_for
from tests.conftest import create_authorization_header

from tests.db import create_event_date


class WhenGettingEventDates(object):

    def it_returns_all_event_dates(self, client, sample_event_date, db_session):
        response = client.get(
            url_for('event_dates.get_event_dates', event_date_id=str(sample_event_date.id)),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        assert len(json_resp) == 1
        assert json_resp[0]['id'] == str(sample_event_date.id)


class WhenGettingEventDateByID(object):

    def it_returns_correct_event_date(self, client, sample_event_date, db_session):
        response = client.get(
            url_for('event_date.get_event_date_by_id', event_date_id=str(sample_event_date.id)),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['id'] == str(sample_event_date.id)


class WhenPostingEventDate(object):

    def it_creates_an_event_date_on_valid_post_data(self, client, db_session, sample_event, sample_venue):
        data = {
            'event_id': str(sample_event.id),
            'event_datetime': '2018-04-11 12:00'
        }

        response = client.post(
            url_for('event_date.create_event_date'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            assert data[key] == json_resp[key]

    def it_doesnt_create_duplicate_event_dates(self, client, db_session, sample_event_date):
        data = {
            'event_id': str(sample_event_date.event_id),
            'event_datetime': sample_event_date.event_datetime.strftime('%Y-%m-%d %H:%M')
        }

        response = client.post(
            url_for('event_date.create_event_date'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == '{} already exists for {}'.format(data['event_datetime'], data['event_id'])

    @pytest.mark.parametrize('data,error_msg', [
        ({'event_id': 'cc23965c-afb2-4c3a-9460-8ad74783b68b'}, 'event_datetime is a required property'),
        ({'event_datetime': '2018-04-11 12:00'}, 'event_id is a required property'),
        (
            {
                'event_id': 'cc23965c-afb2-4c3a-9460-8ad74783b68b',
                'event_datetime': '12:00 2018-04-11'
            },
            'event_datetime is not a datetime in format YYYY-MM-DD HH:MM(:SS)?'
        ),
    ])
    def it_returns_400_on_invalid_event_date_post_data(self, client, data, error_msg, db_session):
        response = client.post(
            url_for('event_date.create_event_date'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert all([e['error'] == "ValidationError" for e in json_resp['errors']])
        assert json_resp['errors'][0]['message'] == error_msg

    def it_updates_an_event_date_on_valid_post_data(self, client, sample_event_date, db_session):
        data = {'event_datetime': '2018-04-12 12:00'}
        response = client.post(
            url_for('event_date.update_event_date', event_date_id=sample_event_date.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            assert data[key] == json_resp[key]

    def it_doesnt_update_duplicate_event_date(self, client, db_session, sample_event_date):
        event_date_1 = create_event_date(event_id=sample_event_date.event_id)

        data = {
            'event_datetime': sample_event_date.event_datetime.strftime('%Y-%m-%d %H:%M')
        }

        response = client.post(
            url_for('event_date.update_event_date', event_date_id=event_date_1.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400
        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == '{} already exists for {}'.format(
            data['event_datetime'], sample_event_date.event_id)
