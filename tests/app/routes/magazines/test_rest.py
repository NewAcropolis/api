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

    def it_creates_a_magazine_and_uploads_it_to_storage(self, mocker, client, db_session):
        mocker_upload = mocker.patch('app.routes.magazines.rest.Storage.upload_blob_from_base64string')
        mocker.patch('app.routes.magazines.rest.Storage.__init__', return_value=None)
        data = {
            'title': 'title',
            'filename': 'Magazine Issue 1.pdf',
            'pdf_data': 'test data'
        }

        response = client.post(
            url_for('magazines.create_magazine'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201
        assert mocker_upload.call_args == call(
            u'Magazine Issue 1.pdf', 'bi_monthly_issue_1.pdf', u'test data', content_type='application/pdf')

    def it_doesnt_creates_a_magazine_if_filename_not_matched(self, client):
        data = {
            'title': 'title',
            'filename': 'Magazine 1.pdf',
            'pdf_data': 'test data'
        }

        response = client.post(
            url_for('magazines.create_magazine'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400


class WhenGettingMagazines(object):

    def it_gets_magazines(self, client, db_session):
        create_magazine(title='title', filename='new filename')
        create_magazine(old_id='2', title='title 2', filename='new filename 2')

        response = client.get(
            url_for('magazines.get_magazines'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200
        assert len(response.json) == 2


class WhenGettingMagazine(object):

    def it_gets_magazine_by_id(self, client, db_session):
        magazine = create_magazine(title='title', filename='new filename')
        create_magazine(old_id='2', title='title 2', filename='new filename 2')

        response = client.get(
            url_for('magazines.get_magazine_by_id', id=magazine.id),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200
        assert response.json['id'] == str(magazine.id)

    def it_gets_magazine_by_old_id(self, client, db_session):
        magazine = create_magazine(old_id='1', title='title', filename='new filename')
        create_magazine(old_id='2', title='title 2', filename='new filename 2')

        response = client.get(
            url_for('magazines.get_magazine_by_old_id', old_id=magazine.old_id),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200
        assert response.json['id'] == str(magazine.id)
