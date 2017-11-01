import pytest

from flask import json, url_for


class WhenAccessingSiteInfo(object):

    def it_shows_info(self, client, db):
        response = client.get(
            url_for('.get_info')
        )
        query = 'SELECT version_num FROM alembic_version'
        version_from_db = db.session.execute(query).fetchone()[0]
        json_resp = json.loads(response.get_data(as_text=True))['info']
        assert response.status_code == 200
        assert json_resp == version_from_db
