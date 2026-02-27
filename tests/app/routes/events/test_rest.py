import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

import base64
import copy
from datetime import timedelta
import pytest
from flask import json, url_for
from uuid import UUID
from mock import Mock, call

from freezegun import freeze_time
from sqlalchemy.orm.exc import NoResultFound

from app.errors import PaypalException
from app.models import Event, EventDate, RejectReason, ReservedPlace, APPROVED, DRAFT, READY, REJECTED

from tests.conftest import create_authorization_header, sample_event_with_dates, TEST_ADMIN_USER
from tests.db import create_event, create_event_date, create_event_type, create_speaker, DATA_MAP

base64img = (
    'iVBORw0KGgoAAAANSUhEUgAAADgAAAAsCAYAAAAwwXuTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAEMElEQVRoge2ZTUxcVRTH'
    '/+fed9+bDxFEQUCmDLWbtibWDE2MCYGa6rabykITA7pV6aruNGlcGFe6c2ui7k1cmZp0YGdR2pjqoklBpkCVykem8/'
    'HeffceF8MgIC3YvDczNP0ls5l3cuf8cuee++65wGMe09LQQQP5xkkXJ4rpjYU40zkY7UcA/NZWopM3gv1iHyg4M5NTuRPrPf5'
    '6cJ4ETgsHg1ZHludDIxQQBphLpOiasfTrtVvPXB4a+nnPzO4rWFnOjroJO25CfkF5UAgBrTm+rP8nyiHAAzgALNNsCHzjdXZdI'
    'dop+h/BmzePeYPd+lXW9pIj4eqAwa3jtSeuV9PQhvKqKC7S4Hy1/myHIHNfSq84nyqXR7Tf+mK7cdMEU6G89O2HlLldAQCxPSD'
    '4U55TaRoJqodPDgCCEkOmaMR38HH9uy3B4tLAceViUt8zzckuInTJwE3QmerikbPApuDaXLbDk3yBCMnDOHPbYQYISEiJC7x6t'
    'F0AQNrzn1dpejnwD7ndJoHPcBKc0WX/uACAkOUr7Ntm5xUp2mdYQR8RAPBa5vqjMnvbceTmGoxajqj2aTah2bVNRAIB1pBmrm3'
    'AzfaMXNBNEqQU3wp2Jo2lWVKbok0yjWUGjWGjeuevyM6Fd2HxgbW4Kh1qiqgT07gEAEQwwO08M6bDu9lhhnnbcWiIBNCod9y4B'
    'HdABAvM55kxFa5khtmIcaVsDhS/aEME6xCBgcIUgCm9lBlmBxNKUQ4UfSWvE/0aPCCqrzDtdhfeCUO8pzX94qp/jz1R0jTBOqq'
    '7MO12L0xUfXq/WsWsktEWoqYL1kn2FaaSvYXxUlVOWkNhVJINXYMPggGqLg+MSrJvMlhGVXhaQlCvDJzRlicSyr5YKzjRjd00Q'
    'WbI8E7/MEkxIaU9BQkEQfSVtOGCvJDps2l6w6ziNSFtRiiObYsAGihYWhnoVYbHNPF5pfhJ6zMMA2HMx7S4BLeyvvdXtsexdgz'
    'WjqkU2sIKIyjH9Kt7EL0gA5aRKC4f61LQ47DmnJdCm26wWB0CAP9O//UoR+TaPqbdJJLN7q/GMoNCsgPACar7RseOAGq9iyhhR'
    'ss0jgUAaI3FVuihRI3rUU1QWL6kYniTbyauR/Cr+FIAgEp5v4dVKsRxXGkGShECjT88Nl8JAKDOWxvG4HNmVB6FvyolBIyhr6l'
    'vqbx1XEo8t3BZB/hCPRFxxWkwtSs0zid7wu+BXedB91nznSlx3k0fzml00wTjU75QFBeJlsrAHje8PJdN6Db7mZI8AsTXK4kSI'
    'QBH0f43vHWYc8pfXRl1gLcE8UukAF1uPVGVItgKw0oqGiM/8bqe/nHfO/rtzMzk1Kmjd8+SNKd1hV4nQKIVPAlgwKgk/6DL8qp'
    'nwp+of/Hv+4QejLW5bEeHsLQRXZoPTTuAdSv4qcH59f1i/wGycsTRKGME7gAAAABJRU5ErkJggg=='
)


def base64img_encoded():
    base64img_encoded = base64.b64encode(base64img.encode())
    base64img_encoded = base64.b64encode(base64img_encoded).decode('utf-8')
    return base64img_encoded


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
            "MultiDayFee": "10",
            "MultiDayConcFee": "8",
            "StartDate": "2004-09-20 19:30:00",
            "StartDate2": "2004-09-21 19:30:00",
            "StartDate3": "2004-09-22 19:30:00",
            "StartDate4": "2004-09-23 19:30:00",
            "EndDate": "0000-00-00 00:00:00",
            "Duration": "0",
            "Fee": "4",
            "ConcFee": "2",
            "Pub-First-Number": "3",
            "Mem-SignOn-Number": "12",
            "ImageFilename": "2004/Economics.jpg",
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
            "ImageFilename": "2004/WinterCourse.jpg",
            "WebLink": "",
            "LinkText": "",
            "MembersOnly": "n",
            "RegisterStartOnly": "0",
            "SoldOut": None
        },
    ]

    return data


@pytest.fixture
def sample_req_event_data(db_session, sample_event_type, sample_venue, sample_speaker):
    return {
        'event_type': sample_event_type,
        'venue': sample_venue,
        'speaker': sample_speaker,
    }


@pytest.fixture
def sample_req_event_data_with_event(db_session, sample_req_event_data, sample_event, sample_event_date):
    data = {
        "event_type_id": sample_req_event_data['event_type'].id,
        "title": "Test title new",
        "sub_title": "Test sub title",
        "description": "Test description",
        "image_filename": "2019/test_img.png",
        "event_dates": [
            {
                "event_date": str(sample_event.event_dates[0].event_datetime),
                "speakers": [
                    {"speaker_id": sample_req_event_data['speaker'].id}
                ]
            },
        ],
        "venue_id": sample_req_event_data['venue'].id,
        "fee": 15,
        "conc_fee": 12,
    }

    sample_event_date.speakers = [sample_req_event_data['speaker']]
    sample_req_event_data['event'] = sample_event
    sample_req_event_data['data'] = data

    return sample_req_event_data


@pytest.fixture
def mock_paypal(mocker):
    return mocker.patch("app.routes.events.rest.PayPal.create_update_paypal_button", return_value='test booking code')


@pytest.fixture
def mock_paypal_task(mocker):
    return mocker.patch('app.routes.events.rest.paypal_tasks.create_update_paypal_button_task.apply_async')


@pytest.fixture
def mock_storage_without_asserts(mocker):
    mocker.patch("app.utils.storage.Storage.__init__", return_value=None)
    mocker.patch("app.utils.storage.Storage.blob_exists", return_value=True)
    mocker.patch("app.utils.storage.Storage.get_blob", return_value=b'test_blob')
    mocker.patch("app.utils.storage.Storage.upload_blob")
    mock_storage_rename = mocker.patch("app.utils.storage.Storage.rename_image")
    mock_storage_generate_web_image = mocker.patch("app.utils.storage.Storage.generate_web_image")

    return {
        'mock_storage_rename': mock_storage_rename,
        'mock_storage_generate_web_image': mock_storage_generate_web_image
    }


class WhenGettingEvents:

    def it_returns_all_events(self, client, sample_event_with_dates, db_session):
        response = client.get(
            url_for('events.get_events'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        data = json.loads(response.get_data(as_text=True))
        assert len(data) == 1

    def it_returns_event_by_id(self, client, sample_event_with_dates, db_session):
        sample_event_with_dates.remote_access = '111'
        sample_event_with_dates.remote_pw = 'pwd'
        response = client.get(
            url_for('events.get_event_by_id', event_id=sample_event_with_dates.id),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        data = json.loads(response.get_data(as_text=True))
        assert data['id'] == str(sample_event_with_dates.id)
        assert data['remote_access'] == '111'
        assert data['remote_pw'] == 'pwd'

    @freeze_time("2018-01-10T19:00:00")
    def it_returns_all_future_events(self, client, sample_event_with_dates, sample_event_type, db_session):
        event_1 = create_event(
            title='future event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2018-01-20T19:00:00')]
        )
        event_2 = create_event(
            title='future event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2018-01-25T19:00:00')]
        )

        response = client.get(
            url_for('events.get_future_events'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        data = json.loads(response.get_data(as_text=True))
        assert Event.query.count() == 3
        assert len(data) == 2
        assert data[0]['id'] == str(event_1.id)
        assert data[1]['id'] == str(event_2.id)
        assert not data[0]['has_expired']
        assert not data[1]['has_expired']

    @freeze_time("2018-01-10T19:00:00")
    def it_returns_past_year_events(self, client, sample_event_with_dates, sample_event_type, db_session):
        create_event(
            title='future event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2018-01-20T19:00:00')]
        )
        create_event(
            title='way past year event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2016-01-25T19:00:00')]
        )

        response = client.get(
            url_for('events.get_past_year_events'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        data = json.loads(response.get_data(as_text=True))
        assert Event.query.count() == 3
        assert len(data) == 1
        assert data[0]['id'] == str(sample_event_with_dates.id)
        assert data[0]['has_expired']

    def it_returns_events_in_year(self, client, sample_event_with_dates, sample_event_type, db_session):
        event_2 = create_event(
            title='2018 event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2018-01-20T19:00:00')]
        )
        create_event(
            title='way past year event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2016-01-25T19:00:00')]
        )

        response = client.get(
            url_for('events.get_events_in_year', year=2018),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        data = json.loads(response.get_data(as_text=True))
        assert Event.query.count() == 3
        assert len(data) == 2
        assert data[0]['id'] == str(event_2.id)
        assert data[1]['id'] == str(sample_event_with_dates.id)

    def it_returns_limited_events(self, client, sample_event_with_dates, sample_event_type, db_session):
        event_2 = create_event(
            title='2018 event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2018-01-20T19:00:00')]
        )
        create_event(
            title='beyond limit',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2016-01-25T19:00:00')]
        )

        response = client.get(
            url_for('events.get_limited_events', limit=2),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        data = json.loads(response.get_data(as_text=True))

        assert Event.query.count() == 3
        assert len(data) == 2
        assert data[0]['id'] == str(event_2.id)
        assert data[1]['id'] == str(sample_event_with_dates.id)

    def it_raises_400_returns_limited_events_more_than_events_max(
        self, client, sample_event_with_dates, sample_event_type, db_session
    ):
        create_event(
            title='2018 event',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2018-01-20T19:00:00')]
        )
        create_event(
            title='beyond limit',
            event_type_id=sample_event_type.id,
            event_dates=[create_event_date(event_datetime='2016-01-25T19:00:00')]
        )

        response = client.get(
            url_for('events.get_limited_events', limit=3),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400

        data = json.loads(response.get_data(as_text=True))

        assert Event.query.count() == 3
        assert len(data) == 2
        assert data['message'] == '3 is greater than events max'

    def it_returns_all_events_with_event_dates(self, client, sample_speaker, sample_event_type, db_session):
        event_date_1 = create_event_date(event_datetime="2018-01-03")
        event_date_earliest = create_event_date(event_datetime="2018-01-01")
        event_date_2 = create_event_date(event_datetime="2018-01-02")

        create_event(event_type_id=sample_event_type.id, event_dates=[event_date_1, event_date_2])
        create_event(event_type_id=sample_event_type.id, event_dates=[event_date_2])
        create_event(event_type_id=sample_event_type.id, event_dates=[event_date_earliest])

        response = client.get(
            url_for('events.get_events'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        data = json.loads(response.get_data(as_text=True))
        assert len(data) == 3
        assert data[0]['event_dates'][0]['event_datetime'] == str(event_date_earliest.event_datetime)[0:-3]


class WhenPostingExtractSpeakers:

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
        assert set([s['name'] for s in json_resp]) == data_speakers


class WhenPostingImportEvents(object):

    @pytest.fixture
    def mock_storage(self, mocker):
        mock_storage = mocker.patch("app.utils.storage.Storage.__init__", return_value=None)
        mock_storage_blob_exists = mocker.patch("app.utils.storage.Storage.blob_exists")
        yield
        mock_storage.assert_called_with('test-store')
        mock_storage_blob_exists.assert_called_with('2004/WinterCourse.jpg')

    @pytest.fixture
    def mock_storage_not_exists(self, mocker):
        mocker.patch('os.path.isfile', return_value=True)
        mock_storage = mocker.patch("app.utils.storage.Storage.__init__", return_value=None)
        mock_storage_blob_exists = mocker.patch("app.utils.storage.Storage.blob_exists", return_value=False)
        mock_storage_blob_upload = mocker.patch("app.utils.storage.Storage.upload_blob")
        yield
        mock_storage.assert_called_with('test-store')
        mock_storage_blob_exists.assert_called_with('2004/Economics.jpg')
        mock_storage_blob_upload.assert_called_with('./data/events/2004/Economics.jpg', '2004/Economics.jpg')

    @pytest.fixture
    def mock_storage_not_exists_without_asserts(self, mocker):
        mocker.patch("app.utils.storage.Storage.__init__", return_value=None)
        mocker.patch("app.utils.storage.Storage.blob_exists", return_value=False)
        mocker.patch("app.utils.storage.Storage.upload_blob")

    def it_creates_events_for_imported_events(
        self, client, db_session, sample_event_type, sample_venue, sample_speaker, sample_data,
        mock_storage
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
            assert json_events[i]["fee"] == int(sample_data[i]["Fee"])
            assert json_events[i]["conc_fee"] == int(sample_data[i]["ConcFee"])
            assert json_events[i]["multi_day_fee"] == int(sample_data[i]["MultiDayFee"])
            assert json_events[i]["multi_day_conc_fee"] == int(sample_data[i]["MultiDayConcFee"])
            assert json_events[i]["venue"]['name'] == sample_venue.name
            assert json_events[i]["venue"]['directions'] == sample_venue.directions

    def it_creates_multiple_speakers_for_imported_events_with_multiple_speakers(
        self, client, db_session, sample_event_type, sample_venue, sample_speaker, sample_data, mock_storage
    ):
        speaker_1 = create_speaker(name='John Smith')
        sample_data[0]['Speaker'] = "{} and {}".format(sample_speaker.name, speaker_1.name)
        sample_data[1]['Speaker'] = sample_speaker.name + " & " + speaker_1.name
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

        speaker_ids = [e['id'] for e in json_events[0]["event_dates"][0]["speakers"]]
        assert str(sample_speaker.id) in speaker_ids
        assert str(speaker_1.id) in speaker_ids

        assert len(json_events[0]["event_dates"]) == 4
        assert json_events[0]["event_dates"][0]['event_datetime'] == "2004-09-20 19:30"
        assert json_events[0]["event_dates"][1]['event_datetime'] == "2004-09-21 19:30"
        assert json_events[0]["event_dates"][2]['event_datetime'] == "2004-09-22 19:30"
        assert json_events[0]["event_dates"][3]['event_datetime'] == "2004-09-23 19:30"

        speaker_ids = [e['id'] for e in json_events[1]["event_dates"][0]["speakers"]]
        assert str(sample_speaker.id) in speaker_ids
        assert str(speaker_1.id) in speaker_ids

    def it_ignores_existing_events_for_imported_events(
        self, client, db_session, sample_event_type, sample_venue, sample_speaker, sample_event, sample_data,
        mock_storage
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

    @pytest.mark.parametrize('field,desc', [
        ('Type', 'event type'),
        ('Speaker', 'speaker'),
        ('venue', 'venue')
    ])
    def it_adds_errors_to_list_for_a_non_existant_field(
        self, client, db_session, sample_event_type, sample_venue, sample_speaker, sample_data, field, desc,
        mock_storage_not_exists
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
        assert str(json_resp['events'][0]["old_id"]) == str(sample_data[0]["id"])
        assert json_resp['errors'][0] == "{} {} not found: 0".format(sample_data[1]["id"], desc)

    def it_adds_errors_to_list_for_a_non_existant_local_filename(
        self, client, mocker, db, db_session, sample_event_type, sample_venue, sample_speaker, sample_data,
        mock_storage_not_exists_without_asserts
    ):
        mocker.patch('os.path.isfile', return_value=False)
        response = client.post(
            url_for('events.import_events'),
            data=json.dumps(sample_data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        assert len(json_resp['events']) == 2
        assert len(json_resp['errors']) == 2
        assert str(json_resp['events'][0]["old_id"]) == str(sample_data[0]["id"])
        assert json_resp['errors'][0] == "./data/events/{} not found for 1".format(sample_data[0]['ImageFilename'])
        assert json_resp['errors'][1] == "./data/events/{} not found for 2".format(sample_data[1]['ImageFilename'])


class WhenPostingCreatingAnEvent:
    # @pytest.fixture
    # def mock_storage_without_asserts(self, mocker):
    #     mocker.patch("app.utils.storage.Storage.__init__", return_value=None)
    #     mocker.patch("app.utils.storage.Storage.upload_blob_from_base64string")

    @pytest.fixture
    def mock_storage(self, mocker):
        mock_storage = mocker.patch("app.utils.storage.Storage.__init__", return_value=None)
        mock_storage_blob_upload = mocker.patch("app.utils.storage.Storage.upload_blob_from_base64string")
        yield
        mock_storage.assert_called_with('test-store')
        for event in Event.query.all():
            if event.image_filename:
                mock_storage_blob_upload.assert_called_with(
                    'test_img.png', '2019/{}'.format(str(event.id)), base64.b64encode(base64img.encode()))

    @pytest.mark.parametrize('mock_state,paypal_button_task_called', [
        (DRAFT, False),
        (READY, True),
        (APPROVED, True)
    ])
    def it_creates_an_event_via_rest(
        self, mocker, client, db_session, sample_req_event_data, mock_storage_without_asserts,
        mock_state, paypal_button_task_called, mock_paypal_task
    ):
        mocker.patch("app.utils.storage.Storage.blob_exists", return_value=True)

        speaker = create_speaker(name='Fred White')

        data = {
            "event_type_id": sample_req_event_data['event_type'].id,
            "title": "Test title",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "2019/test_img.png",
            "event_dates": [
                {
                    "event_date": "2019-03-01 19:00",
                    "end_time": "21:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data['speaker'].id}
                    ]
                },
                {
                    "event_date": "2019-03-02 19:00:00",
                    "end_time": "21:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data['speaker'].id},
                        {"speaker_id": speaker.id}
                    ]
                }
            ],
            "event_state": mock_state,
            "venue_id": sample_req_event_data['venue'].id,
            "fee": 15,
            "conc_fee": 12,
        }

        response = client.post(
            url_for('events.create_event'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 201

        assert paypal_button_task_called == mock_paypal_task.called

        json_events = json.loads(response.get_data(as_text=True))

        assert json_events["title"] == data["title"]
        assert len(json_events["event_dates"]) == 2
        assert len(json_events["event_dates"][0]["speakers"]) == 1
        assert len(json_events["event_dates"][1]["speakers"]) == 2
        assert json_events["event_dates"][0]["end_time"] == '21:00'
        assert json_events["event_dates"][1]["end_time"] == '21:00'
        assert json_events["event_dates"][0]["speakers"][0]['id'] == sample_req_event_data['speaker'].serialize()['id']

        speaker_ids = [e['id'] for e in json_events["event_dates"][1]["speakers"]]
        assert sample_req_event_data['speaker'].serialize()['id'] in speaker_ids
        assert speaker.serialize()['id'] in speaker_ids
        assert json_events["event_state"] == mock_state

        event = Event.query.one()
        assert event.event_dates[0].end_time.strftime('%H:%M') == '21:00'
        assert event.event_dates[1].end_time.strftime('%H:%M') == '21:00'

    def it_creates_an_event_without_speakers_via_rest(
        self, mocker, client, db_session, sample_req_event_data, mock_storage_without_asserts
    ):
        mocker.patch("app.utils.storage.Storage.blob_exists", return_value=True)
        data = {
            "event_type_id": sample_req_event_data['event_type'].id,
            "title": "Test title",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "test_img.png",
            "event_dates": [
                {
                    "event_date": "2019-03-01 19:00:00",
                },
                {
                    "event_date": "2019-03-02 19:00:00",
                }
            ],
            "venue_id": sample_req_event_data['venue'].id,
            "fee": 15,
            "conc_fee": 12,
        }

        response = client.post(
            url_for('events.create_event'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 201

        json_events = json.loads(response.get_data(as_text=True))
        assert json_events["title"] == data["title"]
        assert len(json_events["event_dates"]) == 2
        assert len(json_events["event_dates"][0]["speakers"]) == 0
        assert len(json_events["event_dates"][1]["speakers"]) == 0

    def it_creates_an_event_with_remote_access_login(
        self, mocker, client, db_session, sample_req_event_data, mock_storage_without_asserts
    ):
        mocker.patch("app.utils.storage.Storage.blob_exists", return_value=True)
        data = {
            "event_type_id": sample_req_event_data['event_type'].id,
            "title": "Test title",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "test_img.png",
            "event_dates": [
                {
                    "event_date": "2019-03-01 19:00:00",
                }
            ],
            "venue_id": sample_req_event_data['venue'].id,
            "fee": 15,
            "conc_fee": 12,
            "remote_access": "111",
            "remote_pw": "pwd"
        }

        response = client.post(
            url_for('events.create_event'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 201

        json_events = json.loads(response.get_data(as_text=True))
        assert json_events["title"] == data["title"]
        assert json_events["remote_access"] == data["remote_access"]
        assert json_events["remote_pw"] == data["remote_pw"]

    def it_renames_tmp_directory_and_create_web_images(
        self, mocker, client, db_session, sample_req_event_data_with_event,
        mock_storage_without_asserts
    ):
        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "tmp/11112222",
            "event_dates": [
                {
                    "event_date": "2019-02-10 19:00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data_with_event['speaker'].id}
                    ],
                    "end_time": "20:00"
                },
            ],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "event_state": APPROVED,
        }

        response = client.post(
            url_for('events.create_event'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 201

        assert mock_storage_without_asserts['mock_storage_rename'].called
        assert mock_storage_without_asserts['mock_storage_rename'].call_args == call(
            'tmp/11112222', f"2019/{response.json['id']}")
        assert mock_storage_without_asserts['mock_storage_generate_web_image'].called
        assert response.json['image_filename'].startswith(f"2019/{response.json['id']}")

    def it_handles_error_with_tmp_directory(
        self, mocker, client, db_session, sample_req_event_data_with_event
    ):
        mocker.patch("app.utils.storage.Storage.__init__", return_value=None)
        mocker.patch("app.utils.storage.Storage.get_blob", side_effect=Exception('Storage error'))
        mock_logger = mocker.patch('app.routes.events.rest.current_app.logger.error')
        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "tmp/11112222",
            "event_dates": [
                {
                    "event_date": "2019-02-10 19:00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data_with_event['speaker'].id}
                    ],
                    "end_time": "20:00"
                },
            ],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "event_state": APPROVED,
        }

        client.post(
            url_for('events.create_event'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert mock_logger.called
        assert (mock_logger.call_args[0]) == ('Problem processing images tmp/11112222: Storage error',)

    def it_raises_400_when_missing_required_fields(self, client):
        response = client.post(
            url_for('events.create_event'),
            data='{}',
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400

        data = json.loads(response.get_data(as_text=True))['errors']

        assert len(data) == 5
        assert data == [
            {"message": "event_type_id is a required property", "error": "ValidationError"},
            {"message": "title is a required property", "error": "ValidationError"},
            {"message": "description is a required property", "error": "ValidationError"},
            {"message": "event_dates is a required property", "error": "ValidationError"},
            {"message": "venue_id is a required property", "error": "ValidationError"}
        ]

    def it_raises_400_when_missing_event_date(self, client, db_session, sample_req_event_data):
        data = {
            "event_type_id": sample_req_event_data['event_type'].id,
            "title": "Test title",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "test_img.png",
            "event_dates": [],
            "venue_id": sample_req_event_data['venue'].id,
            "fee": 15,
            "conc_fee": 12,
        }
        response = client.post(
            url_for('events.create_event'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400

        data = json.loads(response.get_data(as_text=True))['errors']

        assert len(data) == 1
        assert data == [
            {"message": "event_dates [] is too short", "error": "ValidationError"},
        ]

    def it_raises_400_when_supply_invalid_event_type_id(self, client, sample_req_event_data, sample_uuid):
        data = {
            "event_type_id": sample_uuid,
            "title": "Test title",
            "description": "Test description",
            "event_dates": [{"event_date": "2019-03-01 19:00:00"}],
            "venue_id": sample_req_event_data['venue'].id,
        }

        response = client.post(
            url_for('events.create_event'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400
        data = json.loads(response.get_data(as_text=True))

        assert data == {"message": "event type not found: {}".format(sample_uuid), "result": "error"}

    def it_raises_400_when_supply_invalid_venue_id(self, client, sample_req_event_data, sample_uuid):
        data = {
            "event_type_id": sample_req_event_data['event_type'].id,
            "title": "Test title",
            "description": "Test description",
            "event_dates": [{"event_date": "2019-03-01 19:00:00"}],
            "venue_id": sample_uuid,
        }

        response = client.post(
            url_for('events.create_event'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400
        data = json.loads(response.get_data(as_text=True))

        assert data == {"message": "venue not found: {}".format(sample_uuid), "result": "error"}

    def it_raises_400_when_creating_event_with_existing_dates_and_venue(
            self, client, sample_req_event_data, sample_event_with_dates
    ):
        data = {
            "event_type_id": sample_req_event_data['event_type'].id,
            "title": "Test title",
            "description": "Test description",
            "event_dates": [{"event_date": str(sample_event_with_dates.event_dates[0].event_datetime)}],
            "venue_id": sample_event_with_dates.venue_id,
        }

        response = client.post(
            url_for('events.create_event'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400
        data = json.loads(response.get_data(as_text=True))
        assert data == {'message': 'Test title not added, already an event on same date and venue', 'result': 'error'}

    @freeze_time("2019-03-01T23:10:00")
    def it_stores_the_image_in_google_store(
        self, client, db_session, sample_req_event_data, mock_storage
    ):
        data = {
            "event_type_id": sample_req_event_data['event_type'].id,
            "title": "Test title",
            "description": "Test description",
            "image_filename": "test_img.png",
            "image_data": base64img_encoded(),
            "event_dates": [
                {
                    "event_date": "2019-03-01 19:00:00",
                },
            ],
            "venue_id": sample_req_event_data['venue'].id,
        }

        response = client.post(
            url_for('events.create_event'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 201
        data = json.loads(response.get_data(as_text=True))
        assert data['image_filename'] == '2019/{}'.format(data['id'])

    def it_does_not_create_a_booking_code_without_fee(
        self, client, db_session, sample_req_event_data, mock_storage
    ):
        data = {
            "event_type_id": sample_req_event_data['event_type'].id,
            "title": "Test title",
            "description": "Test description",
            "event_dates": [
                {
                    "event_date": "2019-03-01 19:00:00",
                },
            ],
            "venue_id": sample_req_event_data['venue'].id,
        }

        response = client.post(
            url_for('events.create_event'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 201
        data = json.loads(response.get_data(as_text=True))
        assert data["booking_code"] == ''

    def it_raises_400_if_image_filename_not_found(
        self, mocker, client, db_session, sample_req_event_data
    ):
        mocker.patch("app.utils.storage.Storage.__init__", return_value=None)
        mocker.patch("app.utils.storage.Storage.blob_exists", return_value=False)
        data = {
            "event_type_id": sample_req_event_data['event_type'].id,
            "title": "Test title",
            "description": "Test description",
            "image_filename": "test_img.png",
            "event_dates": [
                {
                    "event_date": "2019-03-01 19:00:00",
                },
            ],
            "venue_id": sample_req_event_data['venue'].id,
        }

        response = client.post(
            url_for('events.create_event'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400
        data = json.loads(response.get_data(as_text=True))

        assert data == {"message": "test_img.png does not exist", "result": "error"}


class WhenDeletingEvent:

    def it_deletes_an_event(self, client, sample_event, db_session):
        response = client.delete(
            url_for('events.delete_event', event_id=sample_event.id),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 200
        data = json.loads(response.get_data(as_text=True))

        assert data['message'] == "{} deleted".format(sample_event.id)
        assert Event.query.count() == 0

    def it_raises_500_if_deletion_fails_on_event(self, client, mocker, sample_event, db_session):
        mocker.patch("app.routes.events.rest.dao_delete_event")
        response = client.delete(
            url_for('events.delete_event', event_id=sample_event.id),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 500
        data = json.loads(response.get_data(as_text=True))

        assert data['message'] == '{} was not deleted'.format(sample_event.id)


class WhenPostingUpdatingAnEvent:

    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.mock_config = {
            'ENVIRONMENT': 'live',
            'EMAIL_RESTRICT': None,
            'EMAIL_DOMAIN': 'test.com',
            'FRONTEND_ADMIN_URL': 'https://frontend/test',
            'EMAIL_DISABLED': None
        }

        mocker.patch.dict(
            'app.comms.email.current_app.config',
            self.mock_config
        )
        self.mock_send_email = mocker.patch('app.comms.email.requests.post')

    @pytest.fixture
    def mock_storage(self, mocker):
        mock_storage = mocker.patch("app.utils.storage.Storage.__init__", return_value=None)
        mock_storage_blob_exists = mocker.patch("app.utils.storage.Storage.blob_exists")
        yield
        mock_storage.assert_called_with('test-store')
        mock_storage_blob_exists.assert_called_with('2019/test_img.png')

    @pytest.fixture
    def mock_storage_not_exist(self, mocker):
        mock_storage = mocker.patch("app.utils.storage.Storage.__init__", return_value=None)
        mock_storage_blob_exists = mocker.patch("app.utils.storage.Storage.blob_exists", return_value=False)
        yield
        mock_storage.assert_called_with('test-store')
        mock_storage_blob_exists.assert_called_with('2019/test_img.png')

    @pytest.fixture
    def mock_storage_upload(self, mocker):
        mock_storage = mocker.patch("app.utils.storage.Storage.__init__", return_value=None)
        mock_storage_blob_upload = mocker.patch("app.utils.storage.Storage.upload_blob_from_base64string")
        yield
        mock_storage.assert_called_with('test-store')
        for event in Event.query.all():
            if event.image_filename:
                mock_storage_blob_upload.assert_called_with(
                    'test_img.png', '2018/{}-temp'.format(str(event.id)), base64.b64encode(base64img.encode()))

    def it_updates_an_event_via_rest(
        self, mocker, client, db_session, sample_req_event_data_with_event, mock_storage,
        mock_paypal_task, sample_admin_user, sample_email_provider
    ):
        mock_smtp = mocker.patch('app.routes.events.rest.send_smtp_email')
        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "2019/test_img.png",
            "event_dates": [
                {
                    "event_date": "2019-02-10 19:00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data_with_event['speaker'].id}
                    ],
                    "end_time": "20:00"
                },
            ],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "fee": 15,
            "conc_fee": 12,
            "event_state": READY,
            "remote_access": "123",
            "remote_pw": "pwd"
        }

        old_event_date_id = sample_req_event_data_with_event['event'].event_dates[0].id

        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 200

        json_events = json.loads(response.get_data(as_text=True))
        assert mock_paypal_task.call_args == call((json_events['id'],))
        assert json_events["title"] == data["title"]
        assert json_events["image_filename"] == data["image_filename"]
        assert len(json_events["event_dates"]) == 1
        assert len(json_events["event_dates"][0]["speakers"]) == 1
        assert json_events["event_dates"][0]["speakers"][0]['id'] == (
            sample_req_event_data_with_event['speaker'].serialize()['id'])
        assert json_events["event_dates"][0]['end_time'] == "20:00"
        assert json_events['event_state'] == READY

        event_dates = EventDate.query.all()

        assert len(event_dates) == 1
        # use existing event date
        assert event_dates[0].id != old_event_date_id
        assert mock_smtp.called
        assert json_events['remote_access'] == "123"
        assert json_events['remote_pw'] == "pwd"

    def it_updates_an_event_image_without_checking_if_storage_not_set(
        self, mocker, client, db_session, sample_req_event_data_with_event,
        sample_admin_user, sample_email_provider
    ):
        mocker.patch.dict('app.application.config', {
            'STORAGE': 'Nonetest'
        })

        data = {
            "image_filename": "new_image.png"
        }

        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 200

        json_events = json.loads(response.get_data(as_text=True))
        assert json_events["image_filename"] == data["image_filename"]

    def it_rejects_invalid_event_states(
        self, mocker, client, db_session, sample_req_event_data_with_event
    ):
        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "event_dates": [
                {
                    "event_date": "2019-02-10 19:00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data_with_event['speaker'].id}
                    ],
                    "end_time": "20:00"
                },
            ],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "event_state": 'invalid',
        }

        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == "Event state: 'invalid' not valid"

    def it_updates_an_event_to_reject_with_reason(
        self, mocker, client, db, db_session,
        sample_email_provider, sample_req_event_data_with_event, mock_storage, sample_user
    ):
        mock_smtp = mocker.patch('app.routes.events.rest.send_smtp_email')
        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "2019/test_img.png",
            "event_dates": [
                {
                    "event_date": "2019-02-10 19:00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data_with_event['speaker'].id}
                    ],
                    "end_time": "20:00"
                },
            ],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "event_state": REJECTED,
            'reject_reasons': [
                {
                    "reason": 'Test reject',
                    'created_by': str(sample_user.id),
                    'resolved': False,
                }
            ]
        }

        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 200

        reject_reasons = RejectReason.query.all()
        assert len(reject_reasons) == 1
        assert reject_reasons[0].reason == data['reject_reasons'][0]['reason']
        assert reject_reasons[0].resolved == data['reject_reasons'][0]['resolved']
        assert str(reject_reasons[0].created_by) == data['reject_reasons'][0]['created_by']

        assert mock_smtp.called

    def it_updates_an_event_to_reject_resolved(
        self, mocker, client, db_session,
        sample_req_event_data_with_event, mock_storage, sample_reject_reason, sample_user
    ):
        mocker.patch('app.routes.events.rest.send_smtp_email')
        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "2019/test_img.png",
            "event_dates": [
                {
                    "event_date": "2019-02-10 19:00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data_with_event['speaker'].id}
                    ],
                    "end_time": "20:00"
                },
            ],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "event_state": REJECTED,
            'reject_reasons': [
                {
                    "id": str(sample_reject_reason.id),
                    "reason": 'Test reject',
                    'resolved': True,
                },
                {
                    "reason": 'Test reject 2',
                    'resolved': False,
                },
            ]
        }

        reject_reasons = RejectReason.query.all()
        assert len(reject_reasons) == 1
        assert not reject_reasons[0].resolved

        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 200

        reject_reasons = RejectReason.query.all()
        assert len(reject_reasons) == 2
        assert reject_reasons[0].reason == data['reject_reasons'][0]['reason']
        assert reject_reasons[0].resolved == data['reject_reasons'][0]['resolved']

    def it_raises_an_error_if_reject_without_new_reason(
        self, mocker, client, db_session,
        sample_req_event_data_with_event, sample_reject_reason
    ):
        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "2019/test_img.png",
            "event_dates": [
                {
                    "event_date": "2019-02-10 19:00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data_with_event['speaker'].id}
                    ],
                    "end_time": "20:00"
                },
            ],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "event_state": REJECTED,
            'reject_reasons': [
                {
                    "id": str(sample_reject_reason.id),
                    "reason": 'Test reject',
                    'resolved': True,
                },
            ]
        }

        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == 'rejected event requires new reject reason'

    def it_raises_an_error_if_approved_with_reject_reasons(
        self, mocker, client, db_session,
        sample_req_event_data_with_event, sample_reject_reason
    ):
        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "2019/test_img.png",
            "event_dates": [
                {
                    "event_date": "2019-02-10 19:00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data_with_event['speaker'].id}
                    ],
                    "end_time": "20:00"
                },
            ],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "event_state": APPROVED,
            'reject_reasons': [
                {
                    "id": str(sample_reject_reason.id),
                    "reason": 'Test reject',
                    'resolved': False,
                },
            ]
        }

        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == 'approved event should not have any reject reasons'

    def it_renames_temp_image_file_when_approved(
        self, mocker, client, db_session, sample_req_event_data_with_event,
        mock_storage_without_asserts
    ):
        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "2019/XX-temp?111",
            "event_dates": [
                {
                    "event_date": "2019-02-10 19:00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data_with_event['speaker'].id}
                    ],
                    "end_time": "20:00"
                },
            ],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "event_state": APPROVED,
        }

        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 200

        assert mock_storage_without_asserts['mock_storage_rename'].called
        assert mock_storage_without_asserts['mock_storage_rename'].call_args == call('2019/XX-temp', '2019/XX')
        assert response.json['image_filename'] == '2019/XX'

    def it_renames_tmp_directory_and_create_web_images(
        self, mocker, client, db_session, sample_req_event_data_with_event,
        mock_storage_without_asserts
    ):
        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "tmp/11112222",
            "event_dates": [
                {
                    "event_date": "2019-02-10 19:00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data_with_event['speaker'].id}
                    ],
                    "end_time": "20:00"
                },
            ],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "event_state": APPROVED,
        }

        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 200

        assert mock_storage_without_asserts['mock_storage_rename'].called
        assert mock_storage_without_asserts['mock_storage_rename'].call_args == call(
            'tmp/11112222', f"2019/{sample_req_event_data_with_event['event'].id}")
        assert mock_storage_without_asserts['mock_storage_generate_web_image'].called
        assert response.json['image_filename'].startswith(f"2019/{sample_req_event_data_with_event['event'].id}")

    def it_handles_error_with_tmp_directory(
        self, mocker, client, db_session, sample_req_event_data_with_event
    ):
        mocker.patch("app.utils.storage.Storage.__init__", return_value=None)
        mocker.patch("app.utils.storage.Storage.get_blob", side_effect=Exception('Storage error'))
        mock_logger = mocker.patch('app.routes.events.rest.current_app.logger.error')
        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "tmp/11112222",
            "event_dates": [
                {
                    "event_date": "2019-02-10 19:00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data_with_event['speaker'].id}
                    ],
                    "end_time": "20:00"
                },
            ],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "event_state": APPROVED,
        }

        client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert mock_logger.called
        assert (mock_logger.call_args[0]) == ('Problem processing images tmp/11112222: Storage error',)

    def it_logs_warning_if_no_temp_image_file_when_approved(
        self, mocker, client, db_session, sample_req_event_data_with_event,
        mock_storage_without_asserts
    ):
        mock_logger = mocker.patch('app.routes.events.rest.current_app.logger.warn')

        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "2019/XX?111",
            "event_dates": [
                {
                    "event_date": "2019-02-10 19:00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data_with_event['speaker'].id}
                    ],
                    "end_time": "20:00"
                },
            ],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "event_state": APPROVED,
        }

        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 200

        assert not mock_storage_without_asserts['mock_storage_rename'].called
        assert mock_logger.called

    def it_raises_an_error_if_no_event_dates(
        self, mocker, client, db_session,
        sample_req_event_data_with_event, sample_reject_reason
    ):
        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "2019/test_img.png",
            "event_dates": [],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "event_state": DRAFT,
        }

        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == '{} needs an event date'.format(sample_req_event_data_with_event['event'].id)

    def it_updates_an_event_remove_speakers_via_rest(
        self, mocker, client, db_session, sample_req_event_data_with_event, mock_storage
    ):
        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "2019/test_img.png",
            "event_dates": [
                {
                    "event_date": sample_req_event_data_with_event['event'].event_dates[0].event_datetime.strftime(
                        '%Y-%m-%d %H:%M'),
                    "end_time": "00:00",
                    "speakers": []
                },
            ],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "fee": 15,
            "conc_fee": 12,
        }

        old_event_date_id = sample_req_event_data_with_event['event'].event_dates[0].id

        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 200

        json_events = json.loads(response.get_data(as_text=True))
        assert json_events["title"] == data["title"]
        assert json_events["image_filename"] == data["image_filename"]
        assert len(json_events["event_dates"]) == 1
        assert len(json_events["event_dates"][0]["speakers"]) == 0

        event_dates = EventDate.query.all()

        assert len(event_dates) == 1
        assert event_dates[0].speakers == []
        # use existing event date
        assert event_dates[0].id == old_event_date_id

    def it_updates_an_event_remove_a_speaker_via_rest(
        self, mocker, client, db_session, mock_storage
    ):
        speakers = [
            create_speaker(name='John Red'),
            create_speaker(name='Jane White')
        ]
        event_dates = [
            create_event_date(
                event_datetime='2019-02-01 19:00',
                speakers=speakers
            ),
            create_event_date(
                event_datetime='2019-02-02 19:00',
                speakers=speakers
            )
        ]
        event = create_event(
            event_dates=event_dates,
        )

        data = {
            "event_type_id": str(event.event_type_id),
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "2019/test_img.png",
            "event_dates": [
                {
                    "event_date": "2019-02-01 19:00",
                    "end_time": "00:00",
                    "speakers": [
                        {"speaker_id": str(event.event_dates[0].speakers[1].id)},
                    ]
                },
                {
                    "event_date": "2019-02-02 19:00",
                    "end_time": "00:00",
                    "speakers": [
                        {"speaker_id": str(event.event_dates[1].speakers[0].id)},
                        {"speaker_id": str(event.event_dates[1].speakers[1].id)},
                    ]
                },
            ],
            "venue_id": str(event.venue_id),
            "fee": 15,
            "conc_fee": 12,
        }

        old_event_date_id = event.event_dates[0].id

        response = client.post(
            url_for('events.update_event', event_id=event.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 200

        json_events = json.loads(response.get_data(as_text=True))

        assert json_events["title"] == data["title"]
        assert json_events["image_filename"] == data["image_filename"]
        assert len(json_events["event_dates"]) == 2
        assert len(json_events["event_dates"][0]["speakers"]) == 1
        assert len(json_events["event_dates"][1]["speakers"]) == 2

        event_dates = EventDate.query.all()

        assert len(event_dates) == 2
        assert event_dates[0].speakers[0].id in [
            event.event_dates[0].speakers[0].id, event.event_dates[1].speakers[0].id]
        # use existing event date
        assert old_event_date_id in [event_dates[0].id, event_dates[1].id]

    def it_updates_an_event_add_speakers_via_rest(
        self, mocker, client, db_session, sample_req_event_data_with_event, mock_storage_upload
    ):
        speaker = create_speaker(name='Julie White')

        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "test_img.png",
            "image_data": base64img_encoded(),
            "event_dates": [
                {
                    "event_date": sample_req_event_data_with_event['event'].event_dates[0].event_datetime.strftime(
                        '%Y-%m-%d %H:%M'),
                    "end_time": "00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data_with_event['speaker'].id},
                        {"speaker_id": speaker.id}
                    ]
                },
            ],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "fee": 15,
            "conc_fee": 12,
        }

        old_event_date_id = sample_req_event_data_with_event['event'].event_dates[0].id

        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 200

        json_events = json.loads(response.get_data(as_text=True))
        assert json_events["title"] == data["title"]
        assert json_events["image_filename"].split('?')[0] == '2018/{}-temp'.format(
            sample_req_event_data_with_event['event'].id)
        assert len(json_events["event_dates"]) == 1
        assert len(json_events["event_dates"][0]["speakers"]) == 2

        event_dates = EventDate.query.all()

        assert len(event_dates) == 1
        assert len(event_dates[0].speakers) == 2
        # use existing event date
        assert event_dates[0].id == old_event_date_id

    def it_updates_an_event_add_event_dates_via_rest(
        self, mocker, client, db_session, sample_req_event_data_with_event, mock_storage_upload
    ):
        event_datetime = sample_req_event_data_with_event['event'].event_dates[0].event_datetime
        data = {
            "event_type_id": sample_req_event_data_with_event['event_type'].id,
            "title": "Test title new",
            "sub_title": "Test sub title",
            "description": "Test description",
            "image_filename": "test_img.png",
            "image_data": base64img_encoded(),
            "event_dates": [
                {
                    "event_date": event_datetime.strftime('%Y-%m-%d %H:%M'),
                    "end_time": "00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data_with_event['speaker'].id}
                    ]
                },
                {
                    "event_date": (event_datetime + timedelta(days=1)).strftime('%Y-%m-%d %H:%M'),
                    "end_time": "00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data_with_event['speaker'].id}
                    ]
                },
            ],
            "venue_id": sample_req_event_data_with_event['venue'].id,
            "fee": 15,
            "conc_fee": 12,
        }

        old_event_date_id = sample_req_event_data_with_event['event'].event_dates[0].id

        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 200

        json_events = json.loads(response.get_data(as_text=True))
        assert json_events["title"] == data["title"]
        assert json_events["image_filename"].split('?')[0] == '2018/{}-temp'.format(
            sample_req_event_data_with_event['event'].id)
        assert len(json_events["event_dates"]) == 2
        assert len(json_events["event_dates"][0]["speakers"]) == 1

        event_dates = sorted(EventDate.query.all(), key=lambda k: k.event_datetime)

        assert len(event_dates) == 2
        assert len(event_dates[0].speakers) == 1
        # use existing event date
        assert event_dates[0].id == old_event_date_id

    def it_updates_an_event_adding_booking_code_if_no_fee_before_via_rest(
        self, mocker, client, db_session, sample_req_event_data, mock_storage_upload, mock_paypal_task
    ):
        mocker.patch('app.routes.events.rest.send_smtp_email')
        event = create_event(
            event_type_id=sample_req_event_data['event_type'].id,
            event_dates=[
                create_event_date(
                    event_datetime='2018-01-20T19:00:00',
                    speakers=[
                        sample_req_event_data['speaker']
                    ]
                )
            ],
            fee=None,
            conc_fee=None,
            venue_id=sample_req_event_data['venue'].id
        )

        data = {
            "event_type_id": sample_req_event_data['event_type'].id,
            "title": "Test title",
            "sub_title": "Test sub title",
            "description": "Test description",
            "event_dates": [
                {
                    "event_date": str(event.event_dates[0].event_datetime),
                    "end_time": "00:00",
                    "speakers": [
                        {"speaker_id": sample_req_event_data['speaker'].id}
                    ]
                },
            ],
            "venue_id": sample_req_event_data['venue'].id,
            "fee": 15,
            "conc_fee": 12,
            "booking_code": "test booking",
            "event_state": READY
        }

        response = client.post(
            url_for('events.update_event', event_id=event.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 200

        json_events = json.loads(response.get_data(as_text=True))
        assert mock_paypal_task.call_args == call((str(event.id),))
        assert json_events["title"] == data["title"]

    def it_updates_an_event_without_booking_code_if_no_fee(
        self, mocker, client, db_session, sample_req_event_data, mock_storage_upload, mock_paypal_task
    ):
        mocker.patch('app.routes.events.rest.send_smtp_email')
        event = create_event(
            event_type_id=sample_req_event_data['event_type'].id,
            event_dates=[
                create_event_date(
                    event_datetime='2018-01-20T19:00:00',
                    speakers=[
                        sample_req_event_data['speaker']
                    ]
                )
            ],
            fee=None,
            conc_fee=None,
            venue_id=sample_req_event_data['venue'].id
        )

        data = {
            "event_type_id": sample_req_event_data['event_type'].id,
            "title": "Test title",
            "sub_title": "Test sub title",
            "description": "Test description",
            "venue_id": sample_req_event_data['venue'].id,
            "fee": None,
            "conc_fee": None,
            "event_state": READY
        }

        response = client.post(
            url_for('events.update_event', event_id=event.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 200

        json_events = json.loads(response.get_data(as_text=True))
        assert not mock_paypal_task.called
        assert json_events["title"] == data["title"]

    def it_raises_error_if_file_not_found(
        self, mocker, client, db_session, sample_req_event_data_with_event, mock_storage_not_exist
    ):
        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(sample_req_event_data_with_event['data']),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == '2019/test_img.png does not exist'

    def it_raises_error_if_event_not_updated(
        self, mocker, client, db_session, sample_req_event_data_with_event
    ):
        mocker.patch('app.routes.events.rest.dao_update_event', return_value=False)

        response = client.post(
            url_for('events.update_event', event_id=sample_req_event_data_with_event['event'].id),
            data=json.dumps(sample_req_event_data_with_event['data']),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == '{} did not update event'.format(sample_req_event_data_with_event['event'].id)

    def it_raises_error_if_event_not_found(
        self, mocker, client, db_session, sample_req_event_data_with_event, sample_uuid
    ):
        mocker.patch('app.routes.events.rest.dao_get_event_by_id', side_effect=NoResultFound())

        response = client.post(
            url_for('events.update_event', event_id=sample_uuid),
            data=json.dumps(sample_req_event_data_with_event['data']),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))

        assert json_resp['message'] == 'event not found: {}'.format(sample_uuid)


class WhenPostingReservePlace:

    def it_reserves_a_place(self, mocker, client, db_session, sample_event_with_dates):
        mock_send_email = mocker.patch('app.routes.events.rest.send_email')
        data = {
            'name': 'Mr White',
            'email': 'someone@other.com',
            'eventdate_id': str(sample_event_with_dates.event_dates[0].id)
        }
        response = client.post(
            url_for('events.reserve_place'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        reserved_places = ReservedPlace.query.all()

        assert response.json['name'] == data['name']
        assert response.json['event_date'] == '2018-01-01 19:00'
        assert len(reserved_places) == 1
        assert reserved_places[0].name == data['name']
        assert mock_send_email.called_once()
        assert mock_send_email.call_args[0][0] == 'someone@other.com'
        assert mock_send_email.call_args[0][1] == 'Reserved place for: test_title'
        assert (
            'Mr White,<br>Thank you for your reservation of test_title on Monday, 1st of January at 7 PM' in
            mock_send_email.call_args[0][2]
        )

    def it_doesnt_reserve_a_place_again(self, client, db_session, sample_event_with_dates):
        data = {
            'name': 'Mr White',
            'email': 'someone@other.com',
            'eventdate_id': str(sample_event_with_dates.event_dates[0].id)
        }
        response = client.post(
            url_for('events.reserve_place'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        response = client.post(
            url_for('events.reserve_place'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        reserved_places = ReservedPlace.query.all()

        assert response.json['error'] == data['name'] + " has already reserved a place"
        assert len(reserved_places) == 1


class WhenGettingTicketsAndReservePlaces:

    def it_gets_all_tickets_and_reserved_places(
        self, client, db_session, sample_order
    ):
        create_event(
            title='test_title 2',
            description='test description 2',
            event_dates=[create_event_date(event_datetime='2021-09-09 19:00')]
        )

        data = {
            'name': 'Mr White',
            'email': 'someone@other.com',
            'eventdate_id': str(sample_order.tickets[0].event_date.id)
        }
        client.post(
            url_for('events.reserve_place'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        data_2 = {
            'name': 'Mr Blue',
            'email': 'someone@another.com',
            'eventdate_id': str(sample_order.tickets[0].event_date.id)
        }

        client.post(
            url_for('events.reserve_place'),
            data=json.dumps(data_2),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        data_3 = {
            'name': 'Mr Blue',
            'email': 'someone@another.com',
            'eventdate_id': str(sample_order.tickets[0].event.event_dates[1].id)
        }

        client.post(
            url_for('events.reserve_place'),
            data=json.dumps(data_3),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        response = client.get(
            url_for('events.get_tickets_and_reserved_places', eventdate_id=str(sample_order.tickets[0].event_date.id)),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert len(response.json['reserved_places']) == 2
        assert response.json['reserved_places'][0]['event_date']\
            == response.json['reserved_places'][1]['event_date']\
            == '2018-01-01 19:00'
        assert response.json['reserved_places'][0]['event_title']\
            == response.json['reserved_places'][1]['event_title']\
            == sample_order.tickets[0].event.title
        assert len(response.json['tickets']) == 1
        assert response.json['tickets'][0]['event']['title'] == sample_order.tickets[0].event.title


class WhenTestingPaypal:

    def it_creates_a_paypal_button_in_preview(self, mocker, client, sample_uuid, mock_paypal):
        mocker.patch.dict('app.routes.events.rest.current_app.config', {'ENVIRONMENT': 'test'})
        response = client.post(
            url_for('events.create_test_paypal', item_id=sample_uuid),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert mock_paypal.call_args == call(sample_uuid, 'test paypal')
        resp_text = response.get_data(as_text=True)
        assert resp_text == 'test booking code'

    def it_does_not_create_a_paypal_button_in_live(self, mocker, client, sample_uuid, mock_paypal):
        mocker.patch.dict('app.routes.events.rest.current_app.config', {'ENVIRONMENT': 'live'})

        response = client.post(
            url_for('events.create_test_paypal', item_id=sample_uuid),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.get_data(as_text=True) == 'Cannot test paypal on live environment'


class WhenSyncPaypal:

    def it_calls_paypal_task_create_update_paypal_button_task(self, client, mock_paypal_task, sample_uuid):
        response = client.get(
            url_for('events.sync_paypal', event_id=sample_uuid),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert mock_paypal_task.called
