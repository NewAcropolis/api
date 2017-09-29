import pytest
import uuid

from flask import json, url_for
from tests.conftest import request


@pytest.fixture
def get_fees_page(client):
    return request(url_for('fees.get_fees'), client.get)


class WhenGettingFees(object):

    def it_returns_all_fees(self, sample_fee, get_fees_page, db_session):
        data = json.loads(get_fees_page.get_data(as_text=True))['data']
        assert len(data) == 1
        assert data[0]['id'] == str(sample_fee.id)


class WhenGettingFeeByID(object):

    def it_returns_correct_fee(self, client, sample_fee, db_session):
        response = client.get(
            url_for('fee.get_fee_by_id', fee_id=str(sample_fee.id))
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))['data']
        assert json_resp['id'] == str(sample_fee.id)


class WhenPostingFee(object):

    @pytest.mark.parametrize('data', [
        {'fee': 20, 'conc_fee': 15},
        {'fee': 20, 'conc_fee': 15, 'valid_from': "2017-02-01"},
        {'fee': 20, 'conc_fee': 15, 'multi_day_fee': 30, 'multi_day_conc_fee': 20, 'valid_from': "2017-02-01"}
    ])
    def it_creates_a_fee_on_valid_post_data(self, client, data, sample_event_type, db_session):
        data.update({'event_type_id': str(sample_event_type.id)})
        response = client.post(
            url_for('fee.create_fee'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json')]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            assert data[key] == json_resp['data'][key]

    @pytest.mark.parametrize('data,error_msg', [
        ({'fee': 20}, 'event_type_id is a required property'),
        ({'event_type_id': uuid.uuid4(), 'fee': 20}, 'conc_fee is a required property'),
        ({'event_type_id': uuid.uuid4(), 'conc_fee': 15}, 'fee is a required property'),
        ({'event_type_id': uuid.uuid4(), 'fee': 20, 'conc_fee': 15, 'valid_from': "01-01-2017"},
            'valid_from datetime format is invalid. '
            'It must be a valid ISO8601 date time format, https://en.wikipedia.org/wiki/ISO_8601'),
    ])
    def it_returns_400_on_invalid_post_data(self, client, data, error_msg, db_session):
        response = client.post(
            url_for('fee.create_fee'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json')]
        )
        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert all([e['error'] == "ValidationError" for e in json_resp['errors']])
        assert json_resp['errors'][0]['message'] == error_msg

    def it_updates_a_fee_on_valid_post_data(self, client, sample_fee, db_session):
        data = {'fee': 200, 'conc_fee': 150}
        response = client.post(
            url_for('fee.update_fee', fee_id=sample_fee.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json')]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            assert data[key] == json_resp['data'][key]
