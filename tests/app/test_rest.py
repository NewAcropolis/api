from flask import json, url_for
import pytest


@pytest.fixture(scope='function')
def mock_stats(mocker):
    mocker.patch('celery.app.control.Inspect.stats', return_value={'celery@worker-test': 'test'})


class WhenAccessingSiteInfo(object):

    def it_shows_info(self, mock_stats, client, db):
        response = client.get(
            url_for('.get_info')
        )
        query = 'SELECT version_num FROM alembic_version'
        version_from_db = db.session.execute(query).fetchone()[0]
        json_resp = json.loads(response.get_data(as_text=True))
        assert response.status_code == 200
        assert json_resp['info'] == version_from_db
        assert json_resp['workers'] == 'Running'

    def it_shows_db_error(self, mocker, client, db, mock_stats):
        mocker.patch('app.rest.db.session.execute', side_effect=Exception('db error'))
        response = client.get(
            url_for('.get_info')
        )
        json_resp = json.loads(response.get_data(as_text=True))['info']
        assert response.status_code == 200
        assert json_resp == 'Database error, check logs'

    def it_shows_info_without_db(self, mock_stats, app, client):
        response = client.get(
            url_for('.get_info_without_db')
        )
        assert response.status_code == 200
        assert response.json == {
            'environment': 'test',
            'commit': app.config['GITHUB_SHA']
        }
