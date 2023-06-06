import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

import pytest

from flask import json, url_for
from tests.conftest import create_authorization_header

from tests.db import create_fee


class WhenGettingEventTypes(object):

    def it_returns_all_event_types(self, client, sample_event_type, db_session):
        response = client.get(
            url_for('event_types.get_event_types', event_type_id=str(sample_event_type.id)),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        assert len(json_resp) == 1
        assert json_resp[0]['id'] == str(sample_event_type.id)


class WhenGettingEventTypeByID(object):

    def it_returns_correct_event_type(self, client, sample_event_type, db_session):
        response = client.get(
            url_for('event_type.get_event_type_by_id', event_type_id=str(sample_event_type.id))
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['id'] == str(sample_event_type.id)

    def it_returns_correct_event_type_with_fees(self, client, sample_event_type, db_session):
        fees = [
            create_fee(event_type_id=str(sample_event_type.id), valid_from='2017-03-01'),
            create_fee(event_type_id=str(sample_event_type.id), fee=10, conc_fee=7, valid_from='2017-02-01')
        ]

        response = client.get(
            url_for('event_type.get_event_type_by_id', event_type_id=str(sample_event_type.id))
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['id'] == str(sample_event_type.id)

        for i, fee in enumerate(fees):
            assert json_resp['fees'][i]['fee'] == fee.fee
            assert json_resp['fees'][i]['conc_fee'] == fee.conc_fee


class WhenPostingEventTypes(object):

    def it_creates_event_types_for_imported_event_types(self, client, db_session):
        data = [
            {
                "id": "1",
                "EventType": "Talk",
                "Fees": "5",
                "ConcFees": "3",
                "EventDesc": "",
                "EventFilename": None
            },
            {
                "id": "2",
                "EventType": "Introductory Course",
                "Fees": "0",
                "ConcFees": None,
                "EventDesc": "",
                "EventFilename": None
            }
        ]

        response = client.post(
            url_for('event_types.import_event_types'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        assert len(json_resp) == len(data)
        for i in range(0, len(data) - 1):
            assert json_resp[i]["old_id"] == int(data[i]["id"])
            assert json_resp[i]["event_type"] == data[i]["EventType"]

    def it_ignores_existing_event_types_for_imported_event_types(self, client, db_session, sample_event_type):
        data = [
            {
                "id": "1",
                "EventType": sample_event_type.event_type,
                "Fees": "5",
                "ConcFees": "3",
                "EventDesc": "",
                "EventFilename": None
            },
            {
                "id": "2",
                "EventType": "Introductory Course",
                "Fees": "0",
                "ConcFees": None,
                "EventDesc": "",
                "EventFilename": None
            }
        ]

        response = client.post(
            url_for('event_types.import_event_types'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        # should ignore the first data element but create the second one
        assert len(json_resp) == 1
        assert json_resp[0]["old_id"] == int(data[1]["id"])
        assert json_resp[0]["event_type"] == data[1]["EventType"]


class WhenPostingEventType(object):

    @pytest.mark.parametrize('data', [
        {'event_type': 'Seminar'},
        {'event_type': 'Seminar', 'event_desc': 'Seminar test'},
    ])
    def it_creates_an_event_type_on_valid_post_data(self, client, data, db_session):
        response = client.post(
            url_for('event_type.create_event_type'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            assert data[key] == json_resp[key]

    @pytest.mark.parametrize('data,error_msg', [
        ({'event_desc': 'Seminar test'}, 'event_type is a required property'),
    ])
    def it_returns_400_on_invalid_event_type_post_data(self, client, data, error_msg, db_session):
        response = client.post(
            url_for('event_type.create_event_type'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert all([e['error'] == "ValidationError" for e in json_resp['errors']])
        assert json_resp['errors'][0]['message'] == error_msg

    def it_updates_an_event_type_on_valid_post_data(self, client, sample_event_type, db_session):
        data = {'event_desc': 'updated desc', 'duration': 90}
        response = client.post(
            url_for('event_type.update_event_type', event_type_id=sample_event_type.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            assert data[key] == json_resp[key]
