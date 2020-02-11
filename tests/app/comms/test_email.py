from mock import call
import pytest

from app.comms.email import get_email_html, send_email
from app.models import MAGAZINE


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


class WhenGettingEmailHTML:

    def it_gets_list_of_topics_for_magazine_emails(self, mocker, db_session, sample_magazine):
        mock_render_template = mocker.patch('app.comms.email.render_template')
        sample_magazine.topics = "Philosophy: test 1\nCulture: test 2\nArt: test 3"
        get_email_html(MAGAZINE, magazine_id=sample_magazine.id)

        args, kwargs = mock_render_template.call_args
        assert args[0] == 'emails/magazine.html'
        assert kwargs['topics'] == [
            {'description': ' test 1', 'title': 'Philosophy'},
            {'description': ' test 2', 'title': 'Culture'},
            {'description': ' test 3', 'title': 'Art'}
        ]
