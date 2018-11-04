import copy
import pytest
from flask import json, url_for
from tests.conftest import request, create_authorization_header
from tests.db import create_event_type


@pytest.fixture
def events_page(client):
    return request(url_for('events.get_events'), client.get)


@pytest.fixture
def sample_data(sample_speaker):
    create_event_type(old_id=2, event_type='excursion')

    data = [
        {
            "id": "1",
            "BookingCode": "",
            "MemberPay": "0",
            "Approved": "y",
            "Type": "1",
            "Title": "Philosophy of Economics",
            "SubTitle": "",
            "Description": "How Plato and Confucius can help understand economic development",
            "venue": "1",
            "Speaker": sample_speaker.name,
            "MultiDayFee": "0",
            "MultiDayConcFee": "0",
            "StartDate": "2004-09-20 19:30:00",
            "StartDate2": "0000-00-00 00:00:00",
            "StartDate3": "0000-00-00 00:00:00",
            "StartDate4": "0000-00-00 00:00:00",
            "EndDate": "0000-00-00 00:00:00",
            "Duration": "0",
            "Fee": "4",
            "ConcFee": "2",
            "Pub-First-Number": "3",
            "Mem-SignOn-Number": "12",
            "ImageFilename": "2004\/Economics.jpg",
            "WebLink": "",
            "LinkText": None,
            "MembersOnly": "n",
            "RegisterStartOnly": "0",
            "SoldOut": None
        },
        {
            "id": "2",
            "BookingCode": "",
            "MemberPay": "0",
            "Approved": "y",
            "Type": "2",
            "Title": "Study Philosophy",
            "SubTitle": "",
            "Description": "16-week course introducing the major systems of thoughts from the East and West",
            "venue": "1",
            "Speaker": sample_speaker.name,
            "MultiDayFee": None,
            "MultiDayConcFee": "0",
            "StartDate": "2004-09-29 19:30:00",
            "StartDate2": "0000-00-00 00:00:00",
            "StartDate3": "0000-00-00 00:00:00",
            "StartDate4": "0000-00-00 00:00:00",
            "EndDate": "0000-00-00 00:00:00",
            "Duration": "0",
            "Fee": "96",
            "ConcFee": "64",
            "Pub-First-Number": "1",
            "Mem-SignOn-Number": "0",
            "ImageFilename": "2004\/WinterCourse.jpg",
            "WebLink": "",
            "LinkText": "",
            "MembersOnly": "n",
            "RegisterStartOnly": "0",
            "SoldOut": None
        },
    ]

    return data


class WhenGettingEvents(object):

    def it_returns_all_events(self, sample_event, events_page, db_session):
        data = json.loads(events_page.get_data(as_text=True))
        assert len(data) == 1


class WhenPostingExtractSpeakers(object):

    def it_extracts_unique_speakers_from_events_json(self, client, db_session, sample_data):
        event = copy.deepcopy(sample_data[0])
        event['Speaker'] = 'Gary Blue'
        sample_data.append(event)

        response = client.post(
            url_for('events.extract_speakers'),
            data=json.dumps(sample_data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        data_speakers = set([d['Speaker'] for d in sample_data])

        assert len(json_resp) == len(data_speakers)
        assert [s['name'] for s in json_resp] == list(data_speakers)


class WhenPostingImportEvents(object):

    def it_creates_events_for_imported_events(
        self, client, db_session, sample_event_type, sample_venue, sample_speaker, sample_data
    ):
        response = client.post(
            url_for('events.import_events'),
            data=json.dumps(sample_data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_events = json.loads(response.get_data(as_text=True))['events']
        assert len(json_events) == len(sample_data)
        for i in range(0, len(sample_data) - 1):
            assert json_events[i]["old_id"] == int(sample_data[i]["id"])
            assert json_events[i]["title"] == sample_data[i]["Title"]

    def it_ignores_existing_events_for_imported_events(
        self, client, db_session, sample_event_type, sample_venue, sample_speaker, sample_event, sample_data
    ):
        response = client.post(
            url_for('events.import_events'),
            data=json.dumps(sample_data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        # should ignore the first data element but create the second one
        assert len(json_resp['events']) == len(sample_data) - 1
        assert json_resp['events'][0]['title'] == sample_data[1]['Title']
        assert str(json_resp['events'][0]['old_id']) == sample_data[1]['id']

    def it_adds_errors_to_list_for_a_non_existent_event_type(
        self, client, db_session, sample_event_type, sample_venue, sample_speaker, sample_data
    ):
        sample_data[1]['Type'] = "0"
        response = client.post(
            url_for('events.import_events'),
            data=json.dumps(sample_data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        assert len(json_resp['events']) == 1
        assert len(json_resp['errors']) == 1
        assert json_resp['events'][0]["old_id"] == int(sample_data[0]["id"])
        assert json_resp['errors'][0] == "event type not found for id: 0"

    @pytest.mark.parametrize('field,desc', [
        ('Type', 'event type'),
        ('Speaker', 'speaker'),
        ('venue', 'venue')
    ])
    def it_adds_errors_to_list_for_a_non_existent_event_type(
        self, client, db_session, sample_event_type, sample_venue, sample_speaker, sample_data, field, desc
    ):
        sample_data[1][field] = "0"
        response = client.post(
            url_for('events.import_events'),
            data=json.dumps(sample_data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        assert len(json_resp['events']) == 1
        assert len(json_resp['errors']) == 1
        assert json_resp['events'][0]["old_id"] == int(sample_data[0]["id"])
        assert json_resp['errors'][0] == "{} not found: 0".format(desc)
