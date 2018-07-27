import pytest
from flask import json, url_for
from tests.conftest import request, create_authorization_header
from app.models import Venue


@pytest.fixture
def venues_page(client):
    return request(url_for('venues.get_venues'), client.get, headers=[create_authorization_header()])


@pytest.fixture
def venue_page(client):
    return request(url_for('venue.get_venue'), client.get, headers=[create_authorization_header()])


class WhenGettingVenues(object):

    def it_returns_all_venues(self, sample_venue, venues_page, db_session):
        data = json.loads(venues_page.get_data(as_text=True))
        assert len(data) == 1


class WhenGettingVenueByID(object):

    def it_returns_correct_venue(self, client, sample_venue, db_session):
        response = client.get(
            url_for('venue.get_venue_by_id', venue_id=str(sample_venue.id)),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['id'] == str(sample_venue.id)


class WhenPostingVenues(object):

    def it_creates_venues(self, client, db_session):
        data = [
            {
                'name': 'London branch',
                'address': '19 Compton Terrace',
                'directions': 'Nearest station: Highbury & Islington',
                'default': True
            },
            {
                'name': 'Test branch',
                'address': '1 Test Street',
                'directions': 'Nearest station: Teston',
                'default': False
            },
        ]

        response = client.post(
            url_for('venues.create_venues'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        assert len(json_resp) == len(data)
        assert sorted(data) == sorted([
            {
                'name': j['name'],
                'address': j['address'],
                'directions': j['directions'],
                'default': j['default']
            } for j in json_resp])

    def it_creates_venues_only_first_default(self, client, db_session):
        data = [
            {
                'name': 'London branch',
                'address': '19 Compton Terrace',
                'directions': 'Nearest station: Highbury & Islington',
                'default': True
            },
            {
                'name': 'Test branch',
                'address': '1 Test Street',
                'directions': 'Nearest station: Teston',
                'default': True
            },
        ]

        response = client.post(
            url_for('venues.create_venues'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        assert len(json_resp) == len(data)
        assert Venue.query.filter_by(name=data[0]['name']).one().default
        assert not Venue.query.filter_by(name=data[1]['name']).one().default
        assert json_resp[0]['default']
        assert not json_resp[1]['default']

    def it_doesnt_create_duplicate_venues(self, client, db_session, sample_venue):
        data = [{
            'name': sample_venue.name,
            'address': '19 Compton Terrace',
            'directions': 'Nearest station: Highbury & Islington',
            'default': True
        }]

        response = client.post(
            url_for('venues.create_venues'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        assert len(json_resp) == 0


class WhenPostingVenue(object):

    def it_creates_a_venue(self, client, db_session):
        data = {
            'name': 'London branch',
            'address': '19 Compton Terrace',
            'directions': 'Nearest station: Highbury & Islington',
            'default': True
        }

        response = client.post(
            url_for('venue.create_venue'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            assert data[key] == json_resp[key]

    def it_updates_a_venue(self, client, db_session, sample_venue):
        data = {
            'name': 'London branch',
            'address': '19 New Street',
        }

        response = client.post(
            url_for('venue.update_venue', venue_id=sample_venue.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        for key in data.keys():
            assert data[key] == json_resp[key]
