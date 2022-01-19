import base64
import os
from flask import json, url_for
from mock import Mock, call
import pytest
import requests_mock

from app.dao.magazines_dao import dao_get_magazines
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
        mocker_upload = mocker.patch('app.routes.magazines.rest.upload_tasks.upload_magazine.apply_async')

        with open(os.path.join('tests', 'test_files', 'test_magazine.pdf'), encoding='mac_roman', newline='') as f:
            pdf_data = base64.b64encode(f.read().encode('utf-8')).decode('utf-8')

        data = {
            'title': 'title',
            'filename': 'Magazine Issue 1.pdf',
            'pdf_data': pdf_data,
            'tags': 'new tag'
        }

        response = client.post(
            url_for('magazines.create_magazine'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201
        assert pdf_data in mocker_upload.call_args[0][0]
        magazines = dao_get_magazines()
        assert len(magazines) == 1
        magazines[0].tags == 'new tag'

    def it_doesnt_creates_a_magazine_if_filename_not_matched(self, client):
        data = {
            'title': 'title',
            'filename': 'Magazine 1.pdf',
            'pdf_data': 'test data',
            'tags': ''
        }

        response = client.post(
            url_for('magazines.create_magazine'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400

    def it_doesnt_create_a_magazine_if_filename_already_exists(self, mocker, client, db_session):
        magazine = create_magazine(title='title', filename='bi_monthly_issue_1.pdf')

        data = {
            'title': 'new title',
            'filename': magazine.filename,
            'pdf_data': 'test data',
            'tags': 'Philosophy'
        }

        response = client.post(
            url_for('magazines.create_magazine'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400
        assert 'Duplicate key: duplicate key value violates unique constraint "magazines_filename_key"'\
            in response.json['message']

    def it_updates_a_magazine(self, mocker, client, db_session):
        magazine = create_magazine(title='title', filename='new filename')

        mocker_upload = mocker.patch('app.routes.magazines.rest.upload_tasks.upload_magazine.apply_async')

        data = {
            'title': 'new title',
            'filename': 'Magazine Issue 1.pdf',
            'pdf_data': 'test data',
            'topics': '',
            'tags': 'update tag'
        }

        response = client.post(
            url_for('magazines.update_magazine', id=magazine.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200
        assert response.json['title'] == data['title']
        assert data['pdf_data'] in mocker_upload.call_args[0][0]
        magazines = dao_get_magazines()
        assert len(magazines) == 1
        magazines[0].tags == 'update tag'

    def it_updates_a_magazine_without_pdf_data(self, mocker, client, db_session):
        magazine = create_magazine(title='title', filename='new filename')

        mocker_upload = mocker.patch('app.routes.magazines.rest.upload_tasks.upload_magazine.apply_async')
        data = {
            'title': 'new title',
            'filename': 'Magazine Issue 1.pdf',
            'topics': 'philosophy: new world',
            'tags': 'Philosophy'
        }

        response = client.post(
            url_for('magazines.update_magazine', id=magazine.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200
        assert response.json['id'] == str(magazine.id)
        assert response.json['title'] == data['title']
        assert response.json['topics'] == data['topics']
        assert not mocker_upload.called

    def it_doesnt_update_a_magazine_if_filename_not_matched(self, client, db_session):
        magazine = create_magazine(title='title', filename='new filename')
        data = {
            'title': 'title',
            'filename': 'Magazine 1.pdf',
            'pdf_data': 'test data',
            'topics': '',
            'tags': ''
        }

        response = client.post(
            url_for('magazines.update_magazine', id=magazine.id),
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


class WhenGettingLatestMagazine:

    def it_gets_the_latest_magazine(self, client, db_session):
        create_magazine(old_id='1', title='title', filename='new filename')
        magazine = create_magazine(old_id='2', title='title 2', filename='new filename 2')

        response = client.get(
            url_for('magazines.get_latest_magazine', old_id=magazine.old_id),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200
        assert response.json['id'] == str(magazine.id)


class WhenDownloadingMagazine:
    @pytest.fixture
    def mock_storage(self, mocker):
        mocker.patch("app.utils.storage.Storage.__init__", return_value=None)

    def it_downloads_a_pdf(self, app, db_session, client, mocker, mock_storage, sample_magazine):
        mocker.patch("app.utils.storage.Storage.get_blob", return_value=b'Test data')
        mocker.patch.dict('app.application.config', {'ENVIRONMENT': 'development'})

        with requests_mock.mock() as r:
            r.post("http://www.google-analytics.com/collect")

            response = client.get(
                url_for('magazines.download_pdf', magazine_id=sample_magazine.id)
            )

            assert r.last_request.text == "v=1&tid=1&cid=888&t=event&ec=magazine_download&"\
                "ea=download&el=Test+magazine&ev=1"

        assert response.status_code == 200
        assert response.headers['Content-Disposition'] == 'attachment; filename=magazine.pdf'

    def it_logs_missing_tracking_if_ga_response_not_200(
        self, app, db_session, client, mocker, mock_storage, sample_magazine
    ):
        mocker.patch.dict('app.application.config', {'ENVIRONMENT': 'development'})
        mocker.patch("app.utils.storage.Storage.get_blob", return_value=b'Test data')
        mock_logger = mocker.patch("app.routes.magazines.rest.current_app.logger.info")

        with requests_mock.mock() as r:
            r.post("http://www.google-analytics.com/collect", status_code=503)

            response = client.get(
                url_for('magazines.download_pdf', magazine_id=sample_magazine.id)
            )

            assert r.last_request.text == "v=1&tid=1&cid=888&t=event&ec="\
                "magazine_download&ea=download&el=Test+magazine&ev=1"

        assert response.status_code == 200
        assert response.headers['Content-Disposition'] == 'attachment; filename=magazine.pdf'
        assert mock_logger.called
        assert mock_logger.call_args[0][0] == "Failed to track magazine download: magazine_download - Test magazine, 1"
