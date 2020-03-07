from flask import json, url_for
import pytest


class WhenGettingLegacyImages:
    @pytest.fixture
    def mock_storage(self, mocker):
        mocker.patch("app.utils.storage.Storage.__init__", return_value=None)

    def it_gets_a_standard_image(self, client, mocker, mock_storage):
        mock_get_blob = mocker.patch("app.utils.storage.Storage.get_blob", return_value='Test data')

        response = client.get(
            url_for('legacy.image_handler', imagefile='events/2019/test.jpg')
        )

        assert response.status_code == 200
        assert mock_get_blob.call_args[0][0] == 'standard/2019/test.jpg'

    def it_gets_a_thumbnail_image(self, client, mocker, mock_storage):
        mock_get_blob = mocker.patch("app.utils.storage.Storage.get_blob", return_value='Test data')

        response = client.get(
            url_for('legacy.image_handler', imagefile='events/2019/test.jpg', w=100)
        )

        assert response.status_code == 200
        assert mock_get_blob.call_args[0][0] == 'thumbnail/2019/test.jpg'


class WhenGettingLegacyEvent:
    def it_gets_event_with_old_id(self, client, db_session, sample_event):
        response = client.get(
            url_for('legacy.event_handler', eventid=sample_event.old_id)
        )

        assert response.json['id'] == str(sample_event.id)

    def it_raises_a_404_if_not_found(self, client):
        response = client.get(
            url_for('legacy.event_handler', eventid='1')
        )

        assert response.status_code == 404
        assert response.json['message'] == 'event not found for old_id: 1'

    def it_raises_a_400_if_id_not_int(self, client):
        response = client.get(
            url_for('legacy.event_handler', eventid='abc')
        )

        assert response.status_code == 400
        assert response.json['message'] == 'invalid event old_id: abc'

    def it_raises_a_400_if_no_id(self, client):
        response = client.get(
            url_for('legacy.event_handler')
        )

        assert response.status_code == 400
        assert response.json['message'] == 'invalid event old_id: None'
