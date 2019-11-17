from flask import json, url_for
import pytest


class WhenGettingLegacyImages:
    @pytest.fixture
    def mock_storage(self, mocker):
        mocker.patch("app.storage.utils.Storage.__init__", return_value=None)

    def it_gets_a_standard_image(self, client, mocker, mock_storage):
        mock_get_blob = mocker.patch("app.storage.utils.Storage.get_blob", return_value='Test data')

        response = client.get(
            url_for('legacy.image_handler', imagefile='events/2019/test.jpg')
        )

        assert response.status_code == 200
        assert mock_get_blob.call_args[0][0] == 'standard/2019/test.jpg'

    def it_gets_a_thumbnail_image(self, client, mocker, mock_storage):
        mock_get_blob = mocker.patch("app.storage.utils.Storage.get_blob", return_value='Test data')

        response = client.get(
            url_for('legacy.image_handler', imagefile='events/2019/test.jpg', w=100)
        )

        assert response.status_code == 200
        assert mock_get_blob.call_args[0][0] == 'thumbnail/2019/test.jpg'
