from flask import json, url_for
from mock import Mock, call

from tests.conftest import create_authorization_header
from tests.db import create_magazine


class WhenPostingMagazines(object):

    def it_imports_magazine(self, client, db_session):
        data = {
            'old_id': '1',
            'title': 'title',
            'old_filename': 'old filename',
            'filename': 'new filename'
        }

        response = client.post(
            url_for('magazines.import_magazine'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        assert data['old_id'] == str(response.json['old_id'])
        assert data['title'] == response.json['title']


class WhenGettingMagazines(object):

    def it_gets_magazines(self, client, db_session):
        create_magazine(title='title', filename='new filename')
        create_magazine(old_id='2', title='title 2', filename='new filename 2')

        response = client.get(
            url_for('magazines.get_magazines'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200
        assert response.json
        assert len(response.json) == 2
