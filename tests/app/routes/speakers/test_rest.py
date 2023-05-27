import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

import pytest
from flask import json, url_for
from tests.conftest import create_authorization_header
from app.models import Speaker
from tests.db import create_speaker


class WhenGettingSpeakers(object):

    def it_returns_all_speakers(self, client, sample_speaker, db_session):
        response = client.get(
            url_for('speakers.get_speakers'),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        data = json.loads(response.get_data(as_text=True))

        assert len(data) == 1


class WhenPostingSpeakers(object):

    def it_creates_speakers(self, client, db_session):
        data = [
            {'title': 'Mr', 'name': 'Andy Gray'},
            {'title': 'Mrs', 'name': 'Beth Pink'}
        ]

        response = client.post(
            url_for('speakers.create_speakers'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        assert len(json_resp) == len(data)
        # python 3 update code
        assert sorted(data, key=lambda k: k['title']) == \
            sorted([{'title': j['title'], 'name': j['name']} for j in json_resp], key=lambda k: k['title'])

    def it_doesnt_create_speaker_with_same_name(self, client, db_session, sample_speaker):
        data = [
            {'name': sample_speaker.name}
        ]

        response = client.post(
            url_for('speakers.create_speakers'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp == []

        speakers = Speaker.query.all()
        assert len(speakers) == 1
        assert speakers[0].name == sample_speaker.name

    def it_raises_validation_error_on_invalid_speakers(self, client, db_session):
        data = [
            {'title': 'Mr', 'nam': 'Andy Gray'},
            {'title': 'Mrs'}
        ]

        response = client.post(
            url_for('speakers.create_speakers'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert len(json_resp['errors']) == 2
        assert json_resp['errors'][0]['message'] == 'name is a required property'
        assert json_resp['errors'][1]['message'] == '1 name is a required property'

    def it_imports_speakers(self, client, db_session, sample_speaker):
        data = [{'name': 'New Speaker'}, {'title': 'Mrs', 'name': 'New Speaker 2'}]

        response = client.post(
            url_for('speakers.import_speakers'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        speakers = Speaker.query.all()
        assert len(speakers) == 3
        assert speakers[0].name == sample_speaker.name
        assert speakers[1].name == data[0]['name']
        assert speakers[2].name == data[1]['name']

    def it_imports_speakers_with_parent_name(self, client, db_session, sample_speaker):
        data = [{'name': 'New Speaker', 'parent_name': sample_speaker.name}]

        response = client.post(
            url_for('speakers.import_speakers'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        speakers = Speaker.query.all()
        assert len(speakers) == 2
        assert speakers[0].name == sample_speaker.name
        assert speakers[1].name == data[0]['name']
        assert speakers[1].parent_id == sample_speaker.id

    def it_raises_an_error_when_importing_speaker_with_non_existant_parent(self, client, db_session, sample_speaker):
        data = [
            {'name': 'New Speaker', 'parent_name': 'Invalid'}
        ]

        response = client.post(
            url_for('speakers.import_speakers'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400

    def it_raises_an_error_when_importing_existing_speaker(self, client, db_session, sample_speaker):
        data = [
            {'name': sample_speaker.name}
        ]

        response = client.post(
            url_for('speakers.import_speakers'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400

    def it_imports_new_speaker_but_ignores_existing_speaker(self, client, db_session, sample_speaker):
        data = [
            {'name': sample_speaker.name},
            {'name': 'new person'}
        ]

        response = client.post(
            url_for('speakers.import_speakers'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        assert len(json_resp['speakers']) == len(data) - 1
        assert json_resp['speakers'][0]['name'] == data[1]['name']

    def it_raises_an_error_when_importing_speaker_with_parent_speaker_that_has_parent(
        self, client, db_session, sample_speaker
    ):
        speaker = create_speaker(name='New Speaker', parent_id=str(sample_speaker.id))
        data = [
            {'name': 'Another Speaker', 'parent_name': speaker.name}
        ]

        response = client.post(
            url_for('speakers.import_speakers'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400


class WhenGettingSpeakerByID(object):

    def it_returns_correct_speaker(self, client, sample_speaker, db_session):
        response = client.get(
            url_for('speaker.get_speaker_by_id', speaker_id=str(sample_speaker.id)),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['id'] == str(sample_speaker.id)


class WhenPostingSpeaker(object):

    @pytest.mark.parametrize('data', [
        {'title': 'Dr', 'name': 'Sarah Black'},
        {'name': 'Diane Cyan'}
    ])
    def it_creates_a_speaker_on_valid_post_data(self, client, data, db_session):
        response = client.post(
            url_for('speaker.create_speaker'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            assert data[key] == json_resp[key]

    def it_returns_speaker_with_same_name(self, client, db_session, sample_speaker):
        data = {'name': sample_speaker.name}

        response = client.post(
            url_for('speaker.create_speaker'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['id'] == str(sample_speaker.id)

        speakers = Speaker.query.all()
        assert len(speakers) == 1
        assert speakers[0].name == sample_speaker.name

    @pytest.mark.parametrize('data,error_msg', [
        ({'title': 'Mrs'}, 'name is a required property'),
        # ({'titl': 'Ms', 'name': 'Diane Cyan'}, 'test')  # should be able to handle type errors
    ])
    def it_returns_400_on_invalid_post_speaker_data(self, client, data, error_msg, db_session):
        response = client.post(
            url_for('speaker.create_speaker'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert all([e['error'] == "ValidationError" for e in json_resp['errors']])
        assert json_resp['errors'][0]['message'] == error_msg

    def it_updates_a_speaker_on_valid_post_data(self, client, sample_speaker, db_session):
        data = {'title': 'Dr', 'name': 'Sarah Black'}
        response = client.post(
            url_for('speaker.update_speaker', speaker_id=sample_speaker.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            assert data[key] == json_resp[key]
