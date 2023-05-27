import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask import json, url_for
from tests.conftest import create_authorization_header

from app.models import Marketing


class WhenGetingMarketings:

    def it_gets_the_marketings(self, client, db_session, sample_marketing):
        response = client.get(
            url_for('marketings.get_marketings'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]['id'] == str(sample_marketing.id)


class WhenPostingMarketings:

    def it_imports_marketings(self, client, db_session):
        data = [
            {
                "id": "1",
                "marketingtxt": 'Poster',
                "ordernum": "0",
                "visible": "1"
            },
            {
                "id": "2",
                "marketingtxt": 'Leaflet',
                "ordernum": "1",
                "visible": "1"
            },
        ]
        response = client.post(
            url_for('marketings.import_marketings'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        marketings = Marketing.query.all()

        assert len(marketings) == 2
        assert marketings[0].old_id == int(data[0]['id'])
        assert marketings[0].description == data[0]['marketingtxt']
        assert marketings[0].order_number == int(data[0]['ordernum'])
        assert marketings[0].active == (data[0]['visible'] == '1')

    def it_doesnt_import_exising_marketings(self, client, db_session, sample_marketing):
        data = [
            {
                "id": "1",
                "marketingtxt": 'Leaflet',
                "ordernum": "0",
                "visible": "1"
            },
            {
                "id": "2",
                "marketingtxt": 'Poster',
                "ordernum": "1",
                "visible": "1"
            },
        ]
        response = client.post(
            url_for('marketings.import_marketings'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201
        assert response.json.get('errors') == ['marketing already exists: 1']

        marketings = Marketing.query.all()

        assert len(marketings) == 2
