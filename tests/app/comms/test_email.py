from mock import call
import pytest

from app.comms.email import send_email


@pytest.fixture
def mock_config(mocker):
    mocker.patch(
        'flask.current_app.config',
        {
            'DEBUG': True,
            'EMAIL_DOMAIN': 'example.com',
            'EMAIL_PROVIDER_URL': '',
            'EMAIL_PROVIDER_APIKEY': '',
            'TEST_EMAIL': 'test@example.com',
            'ENVIRONMENT': 'test'
        }
    )


@pytest.fixture
def mock_config_live(mocker):
    mocker.patch(
        'flask.current_app.config',
        {
            'DEBUG': True,
            'EMAIL_DOMAIN': 'example.com',
            'EMAIL_PROVIDER_URL': '',
            'EMAIL_PROVIDER_APIKEY': '',
            'TEST_EMAIL': 'test@example.com',
            'ENVIRONMENT': 'live'
        }
    )


@pytest.fixture
def mock_config_restricted(mocker):
    mocker.patch(
        'flask.current_app.config',
        {
            'DEBUG': True,
            'EMAIL_DOMAIN': 'example.com',
            'EMAIL_PROVIDER_URL': '',
            'EMAIL_PROVIDER_APIKEY': '',
            'TEST_EMAIL': 'test@example.com',
            'ENVIRONMENT': 'live',
            'EMAIL_RESTRICT': 1
        }
    )


class WhenSendingAnEmail:

    def it_logs_the_email_if_no_email_config_and_sets_email_to_test_if_not_live(self, app, mocker, mock_config):
        mock_logger = mocker.patch('app.comms.email.current_app.logger.info')
        send_email('someone@example.com', 'test subject', 'test message')

        assert mock_logger.call_args == call(
            "Email not configured, email would have sent: {'to': 'test@example.com', 'html': 'test message',"
            " 'from': 'noreply@example.com', 'subject': 'test subject'}")

    def it_logs_the_email_if_no_email_config_and_sets_real_email_in_live(self, app, mocker, mock_config_live):
        mock_logger = mocker.patch('app.comms.email.current_app.logger.info')
        send_email('someone@example.com', 'test subject', 'test message')

        assert mock_logger.call_args == call(
            "Email not configured, email would have sent: {'to': 'someone@example.com', 'html': 'test message',"
            " 'from': 'noreply@example.com', 'subject': 'test subject'}")

    def it_sends_email_to_test_email_if_email_restricted(self, app, mocker, mock_config_restricted):
        mock_logger = mocker.patch('app.comms.email.current_app.logger.info')
        send_email('someone@example.com', 'test subject', 'test message')

        assert mock_logger.call_args == call(
            "Email not configured, email would have sent: {'to': 'test@example.com', 'html': 'test message',"
            " 'from': 'noreply@example.com', 'subject': 'test subject'}")
