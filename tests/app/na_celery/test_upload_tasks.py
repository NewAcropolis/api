from app.models import MAGAZINE
from app.na_celery.upload_tasks import upload_magazine
from tests.db import create_email


class WhenUploadingMagazinePdfs:

    def it_uploads_a_magazine_pdf_and_sends_email(self, db_session, mocker, sample_magazine, sample_user):
        mocker.patch('app.na_celery.upload_tasks.Storage')
        mocker.patch('app.na_celery.upload_tasks.base64')
        mocker.patch('app.na_celery.upload_tasks.extract_topics', return_value='Philosophy: Meaning of Life And Death')
        mock_send_email = mocker.patch('app.na_celery.upload_tasks.send_email')

        upload_magazine(sample_magazine.id, 'pdf data')

        assert mock_send_email.called

    def it_uploads_a_magazine_pdf_and_reuses_email(self, app, db_session, mocker, sample_magazine, sample_user):
        mocker.patch('app.na_celery.upload_tasks.Storage')
        mocker.patch('app.na_celery.upload_tasks.base64')
        mocker.patch('app.na_celery.upload_tasks.extract_topics', return_value='Philosophy: Meaning of Life And Death')
        mock_send_email = mocker.patch('app.na_celery.upload_tasks.send_email', return_value=200)
        email = create_email(magazine_id=sample_magazine.id, email_type=MAGAZINE)

        upload_magazine(sample_magazine.id, 'pdf data')

        assert mock_send_email.called
        assert '<div>Please review this email: {}/emails/{}</div>'.format(
            app.config['FRONTEND_ADMIN_URL'], str(email.id)) in mock_send_email.call_args[0][2]

    def it_logs_errors(self, app, db_session, mocker, sample_magazine, sample_uuid):
        mocker.patch('app.na_celery.upload_tasks.dao_get_magazine_by_id')
        mock_logger = mocker.patch('app.na_celery.upload_tasks.current_app.logger.error')

        upload_magazine(sample_uuid, 'pdf data')

        assert mock_logger.called
        assert 'Task error uploading magazine' in mock_logger.call_args[0][0]
