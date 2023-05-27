import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

import pytest
from flask import json, url_for
from tests.conftest import create_authorization_header
from app.models import Venue


class WhenGettingVenues(object):

    def it_returns_all_venues(self, client, sample_venue, db_session):
        response = client.get(
            url_for('venues.get_venues'),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        data = json.loads(response.get_data(as_text=True))
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
        # python 3 udpate code?
        assert sorted(data, key=lambda k: k['name']) == sorted([
            {
                'name': j['name'],
                'address': j['address'],
                'directions': j['directions'],
                'default': j['default']
            } for j in json_resp], key=lambda k: k['name'])

    def it_creates_venues_for_imported_venues(self, client, db_session):
        data = [
            {
                "id": "1",
                "name": "",
                "address": "19 Compton Terrace N1 2UN, next door to Union Chapel.",
                "tube": "Highbury & Islington (Victoria Line), 2 minutes walk",
                "bus": "Bus routes 4, 19, 30, 43 & 277 stop nearby"
            },
            {
                "id": "2",
                "name": "Bristol",
                "address": "Caf\u00e9 Revival, 56 Corn Street, Bristol, BS1 1JG",
                "tube": "",
                "bus": ""
            }
        ]

        response = client.post(
            url_for('venues.import_venues'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        assert len(json_resp) == len(data)
        for i in range(0, len(data) - 1):
            assert json_resp[i]["old_id"] == int(data[i]["id"])
            assert json_resp[i]["name"] == data[i]["name"] if data[i]["name"] else 'Head branch'
            assert json_resp[i]["address"] == data[i]["address"]
            assert json_resp[i]["directions"] == "<div>Bus: {bus}</div><div>Train: {train}</div>".format(
                bus=data[i]["bus"], train=data[i]["tube"])

    def it_does_not_create_venue_with_existing_name(self, client, db_session, sample_venue):
        data = [
            {
                "id": "1",
                "name": sample_venue.name,
                "address": "19 Compton Terrace N1 2UN, next door to Union Chapel.",
                "tube": "Highbury & Islington (Victoria Line), 2 minutes walk",
                "bus": "Bus routes 4, 19, 30, 43 & 277 stop nearby"
            }
        ]

        response = client.post(
            url_for('venues.import_venues'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        json_resp = json.loads(response.get_data(as_text=True))

        assert response.status_code == 201
        assert json_resp == []
        assert len(Venue.query.all()) == 1

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
