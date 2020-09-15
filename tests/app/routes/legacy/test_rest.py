from flask import json, url_for
import pytest
import requests_mock

from app.comms.encryption import encrypt


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

    def it_gets_a_pdf_image(self, client, mocker, mock_storage):
        mock_get_blob = mocker.patch("app.utils.storage.Storage.get_blob", return_value='Test data')

        response = client.get(
            url_for('legacy.image_handler', imagefile='Bi_Monthly_Issue 1.pdf')
        )

        assert response.status_code == 200
        assert mock_get_blob.call_args[0][0] == 'standard/pdfs/bi_monthly_issue_1.pdf.png'


class WhenGettingLegacyEvent:
    def it_gets_event_with_old_id(self, client, db_session, sample_event_with_dates):
        response = client.get(
            url_for('legacy.event_handler', eventid=sample_event_with_dates.old_id)
        )

        assert response.json['id'] == str(sample_event_with_dates.id)

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


class WhenGettingLegacyPDFs:
    @pytest.fixture
    def mock_storage(self, mocker):
        mocker.patch("app.utils.storage.Storage.__init__", return_value=None)

    def it_downloads_a_pdf(self, app, db_session, client, mocker, mock_storage, sample_member, sample_magazine):
        enc_member_id = encrypt(
            "{}={}".format(app.config['EMAIL_TOKENS']['member_id'], str(sample_member.id)),
            app.config['EMAIL_UNSUB_SALT']
        )

        mocker.patch("app.utils.storage.Storage.get_blob", return_value=b'Test data')

        with requests_mock.mock() as r:
            r.post("http://www.google-analytics.com/collect")

            response = client.get(
                url_for('legacy.download_pdf_handler', enc=enc_member_id, id=sample_magazine.old_id)
            )
            assert r.last_request.text == "v=1&cid=888&t=event&ec=legacy_magazine_email&ea=download&el=Test+magazine"

        assert response.status_code == 200
        assert response.headers['Content-Disposition'] == 'attachment; filename=magazine.pdf'
