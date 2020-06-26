from mock import call
import pytest
import requests_mock
from urllib import urlencode

from tests.conftest import TEST_DATABASE_URI
from app.comms.email import get_email_html, send_email, get_email_data
from app.dao.email_providers_dao import dao_update_email_provider
from tests.db import create_email_provider
from app.errors import InvalidRequest
from app.models import MAGAZINE, EmailProvider, Email


@pytest.fixture
def mock_config_live(app):
    old_config = app.config
    app.config['ENVIRONMENT'] = 'live'
    yield

    app.config = old_config


@pytest.fixture
def mock_config_restricted(app):
    old_config = app.config
    app.config['ENVIRONMENT'] = 'live'
    app.config['EMAIL_RESTRICT'] = 1
    yield

    app.config = old_config


class WhenSendingAnEmail:
    def it_logs_the_email_if_no_email_config_and_sets_email_to_test_if_not_live(
        self, mocker, client, app, db_session
    ):
        mock_logger = mocker.patch('app.comms.email.current_app.logger.info')

        send_email('someone@example.com', 'test subject', 'test message')

        assert mock_logger.call_args == call(
            "No email providers configured, email would have sent: {'to': 'test@example.com', "
            "'message': 'test message', 'from': 'noreply@example.com', 'subject': 'test subject'}")

    def it_logs_the_email_if_no_email_config_and_sets_real_email_in_live(
        self, app, db_session, mocker, mock_config_live
    ):
        mock_logger = mocker.patch('app.comms.email.current_app.logger.info')
        send_email('someone@example.com', 'test subject', 'test message')

        assert mock_logger.call_args == call(
            "No email providers configured, email would have sent: {'to': 'someone@example.com', "
            "'message': 'test message', 'from': 'noreply@example.com', 'subject': 'test subject'}")

    def it_sends_email_to_test_email_if_email_restricted(self, mocker, db_session, mock_config_restricted):
        mock_logger = mocker.patch('app.comms.email.current_app.logger.info')

        send_email('someone@example.com', 'test subject', 'test message')

        assert mock_logger.call_args == call(
            "No email providers configured, email would have sent: {'to': 'test@example.com', "
            "'message': 'test message', 'from': 'noreply@example.com', 'subject': 'test subject'}")

    def it_sends_email_to_provider(self, mocker, db_session, sample_email_provider):
        with requests_mock.mock() as r:
            r.post(sample_email_provider.api_url, text='OK')
            send_email('someone@example.com', 'test subject', 'test message')

            data = get_email_data(
                sample_email_provider.data_struct,
                'test@example.com',
                'test subject',
                'test message',
                'noreply@example.com'
            )

            assert r.last_request.text == urlencode(data)

    def it_triggers_429_when_daily_limit_reached(self, mocker, db_session, sample_email_provider):
        mocker.patch('app.comms.email.dao_get_todays_email_count_for_provider', return_value=30)

        with pytest.raises(expected_exception=InvalidRequest):
            send_email('someone@example.com', 'test subject', 'test message')

    def it_uses_the_next_email_provider_if_available(self, mocker, db_session, sample_email_provider):
        mocker.patch('app.comms.email.dao_get_todays_email_count_for_provider', return_value=30)
        next_email_provider = create_email_provider(name='Next email provider', daily_limit=100)

        with requests_mock.mock() as r:
            r.post(next_email_provider.api_url, text='OK')
            resp = send_email('someone@example.com', 'test subject', 'test message')

            assert resp == 200

    def it_triggers_429_when_next_email_provider_hits_limit(self, mocker, db_session, sample_email_provider):
        mocker.patch('app.comms.email.dao_get_todays_email_count_for_provider', return_value=30)
        create_email_provider(name='Next email provider', daily_limit=30)
        with pytest.raises(expected_exception=InvalidRequest):
            send_email('someone@example.com', 'test subject', 'test message')

    def it_sends_the_email_with_override(self, mocker, db_session, sample_email_provider):
        mocker.patch('app.comms.email.dao_get_todays_email_count_for_provider', return_value=30)
        with requests_mock.mock() as r:
            r.post(sample_email_provider.api_url, text='OK')
            resp = send_email('someone@example.com', 'test subject', 'test message', override=True)

            assert resp == 200

    def it_sends_the_email_using_next_provider_with_override(self, mocker, db_session, sample_email_provider):
        mocker.patch('app.comms.email.dao_get_todays_email_count_for_provider', return_value=30)
        next_email_provider = create_email_provider(name='Next email provider', daily_limit=30)
        with requests_mock.mock() as r:
            r.post(next_email_provider.api_url, text='OK')
            resp = send_email('someone@example.com', 'test subject', 'test message', override=True)

            assert resp == 200


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
