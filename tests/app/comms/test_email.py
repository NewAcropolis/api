from mock import call
import json
import pytest
import requests_mock
from urllib.parse import urlencode

from tests.conftest import TEST_DATABASE_URI
from app.comms.email import get_email_html, send_email, get_email_data
from app.dao.email_providers_dao import dao_update_email_provider, dao_get_email_provider_by_id
from tests.db import create_email_provider
from app.errors import InvalidRequest
from app.models import API_AUTH, BEARER_AUTH, MAGAZINE, EmailProvider, Email


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


@pytest.fixture
def mock_config_disabled(app):
    old_config = app.config
    app.config['EMAIL_DISABLED'] = 1
    yield

    app.config = old_config


def mock_get_todays_email_count_for_provider_over_first_limit(email_provider_id):
    email_provider = dao_get_email_provider_by_id(email_provider_id)
    if email_provider.pos == 0:
        return email_provider.daily_limit + 1
    else:
        return 0


def mock_get_past_hour_email_count_for_provider_over_first_limit(email_provider_id):
    email_provider = dao_get_email_provider_by_id(email_provider_id)
    if email_provider.pos == 0:
        return email_provider.hourly_limit + 1
    else:
        return 0


class WhenSendingAnEmail:
    def it_logs_the_email_if_no_email_config_and_sets_email_to_test_if_not_live(
        self, mocker, client, app, db_session
    ):
        mock_logger = mocker.patch('app.comms.email.current_app.logger.info')

        send_email('someone@example.com', 'test subject', 'test message')

        assert mock_logger.call_args == call(
            "No email providers configured, email would have sent: {'to': 'test@example.com', "
            "'from_email': 'noreply@example.com', 'from_name': 'New Acropolis', 'subject': 'test subject', "
            "'message': 'test message'}")

    def it_logs_the_email_if_no_email_config_and_sets_real_email_in_live(
        self, app, db_session, mocker, mock_config_live
    ):
        mock_logger = mocker.patch('app.comms.email.current_app.logger.info')
        send_email('someone@example.com', 'test subject', 'test message')

        assert mock_logger.call_args == call(
            "No email providers configured, email would have sent: {'to': 'someone@example.com', "
            "'from_email': 'noreply@example.com', 'from_name': 'New Acropolis', 'subject': 'test subject', "
            "'message': 'test message'}")

    @pytest.mark.parametrize('email,expected_email', [
        ('someone@other.com', 'test@example.com'),
        ('someone+test+again@example.com', 'test@example.com'),
        ('someone+test@example.com', 'someone+test@example.com'),
    ])
    def it_sends_email_to_test_email_if_email_restricted(
        self, mocker, db_session, mock_config_restricted, email, expected_email
    ):
        mock_logger = mocker.patch('app.comms.email.current_app.logger.info')

        send_email(email, 'test subject', 'test message')

        assert mock_logger.call_args == call(
            "No email providers configured, email would have sent: {'to': '" + expected_email + "', "
            "'from_email': 'noreply@example.com', 'from_name': 'New Acropolis', 'subject': 'test subject', "
            "'message': 'test message'}")

    def it_sends_email_to_provider(self, mocker, db_session, sample_email_provider):
        with requests_mock.mock() as r:
            r.post(sample_email_provider.api_url, text='OK')
            send_email('someone@example.com', 'test subject', 'test message')

            data = get_email_data(
                sample_email_provider.data_map,
                'test@example.com',
                'test subject',
                'test message',
                'noreply@example.com',
                'Test'
            )

            assert r.last_request.text == json.dumps(data)

    @pytest.mark.parametrize('auth_type,expected_header', [
        (API_AUTH, 'api-key'),
        (BEARER_AUTH, 'Authorization'),
    ])
    def it_sends_email_to_provider_with_correct_auth(
        self, mocker, db_session, sample_email_provider, auth_type, expected_header
    ):
        sample_email_provider.auth_type = auth_type
        with requests_mock.mock() as r:
            r.post(sample_email_provider.api_url, text='OK')
            send_email('someone@example.com', 'test subject', 'test message')

            assert expected_header in r.last_request.headers.keys()

    def it_sends_email_to_provider_with_smtp(self, mocker, db_session, sample_email_provider):
        sample_email_provider.smtp_server = "http://smtp_server.com"
        sample_email_provider.smtp_user = "user"
        sample_email_provider.smtp_password = "password"

        mock_smtp = mocker.patch('app.comms.email.send_smtp_email')

        send_email('someone@example.com', 'test subject', 'test message')

        assert mock_smtp.called
        assert mock_smtp.call_args == call(
            'test@example.com',
            'test subject',
            'test message',
            from_name='New Acropolis',
            smtp_info={'SMTP_SERVER': 'http://smtp_server.com', 'SMTP_USER': 'user', 'SMTP_PASS': 'password'}
        )

    def it_triggers_429_when_monthly_limit_reached(self, mocker, db_session):
        create_email_provider(monthly_limit=100)
        mocker.patch('app.comms.email.dao_get_last_30_days_email_count_for_provider', return_value=200)

        with pytest.raises(expected_exception=InvalidRequest):
            send_email('someone@example.com', 'test subject', 'test message')

    def it_triggers_429_when_hourly_limit_reached(self, mocker, db_session, sample_email_provider):
        mocker.patch('app.comms.email.dao_get_past_hour_email_count_for_provider', return_value=30)

        with pytest.raises(expected_exception=InvalidRequest):
            send_email('someone@example.com', 'test subject', 'test message')

    def it_triggers_429_when_minute_limit_reached(self, mocker, db_session):
        create_email_provider(minute_limit=5)
        mocker.patch('app.comms.email.dao_get_last_minute_email_count_for_provider', return_value=6)

        with pytest.raises(expected_exception=InvalidRequest):
            send_email('someone@example.com', 'test subject', 'test message')

    def it_triggers_429_when_daily_limit_reached(self, mocker, db_session, sample_email_provider):
        mocker.patch('app.comms.email.dao_get_todays_email_count_for_provider', return_value=30)

        with pytest.raises(expected_exception=InvalidRequest):
            send_email('someone@example.com', 'test subject', 'test message')

    def it_uses_the_next_email_provider_if_available_with_override(self, mocker, db_session, sample_email_provider):
        mocker.patch('app.comms.email.dao_get_todays_email_count_for_provider', return_value=30)
        next_email_provider = create_email_provider(name='Next email provider', daily_limit=100)

        with requests_mock.mock() as r:
            r.post(next_email_provider.api_url, text='OK')
            resp = send_email('someone@example.com', 'test subject', 'test message', override=True)

            assert resp == (200, next_email_provider.id)

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

            assert resp == (200, sample_email_provider.id)

    def it_sends_the_email_with_override_for_hourly_limit_reached(self, mocker, db_session, sample_email_provider):
        mocker.patch(
            'app.comms.email.dao_get_past_hour_email_count_for_provider',
            mock_get_todays_email_count_for_provider_over_first_limit
        )

        next_provider = create_email_provider(name='next provider', pos=2)
        with requests_mock.mock() as r:
            r.post(next_provider.api_url, text='OK')
            resp = send_email('someone@example.com', 'test subject', 'test message', override=True)

            assert resp == (200, next_provider.id)

    def it_sends_the_email_using_next_provider_with_override(self, mocker, db_session, sample_email_provider):
        mocker.patch(
            'app.comms.email.dao_get_todays_email_count_for_provider',
            mock_get_todays_email_count_for_provider_over_first_limit
        )
        next_email_provider = create_email_provider(name='Next email provider', daily_limit=30)
        with requests_mock.mock() as r:
            r.post(next_email_provider.api_url, text='OK')
            resp = send_email('someone@example.com', 'test subject', 'test message', override=True)

            assert resp == (200, next_email_provider.id)

    def it_sends_the_email_using_next_available_provider(self, mocker, db_session, sample_email_provider):
        mocker.patch(
            'app.comms.email.dao_get_todays_email_count_for_provider',
            mock_get_todays_email_count_for_provider_over_first_limit
        )

        create_email_provider(
            name='Next unavailable email provider', hourly_limit=30, pos=3)

        next_available_email_provider = create_email_provider(
            name='Next email provider', hourly_limit=30, pos=5, available=True)

        with requests_mock.mock() as r:
            r.post(next_available_email_provider.api_url, text='OK')
            resp = send_email('someone@example.com', 'test subject', 'test message')

            assert resp == (200, next_available_email_provider.id)

    def it_sends_the_email_using_next_available_provider_hourly_limit(self, mocker, db_session):
        mocker.patch(
            'app.comms.email.dao_get_past_hour_email_count_for_provider',
            mock_get_past_hour_email_count_for_provider_over_first_limit
        )

        create_email_provider(
            name='First email provider', daily_limit=0, hourly_limit=30, pos=0)

        create_email_provider(
            name='Another email provider', daily_limit=0, hourly_limit=30, pos=3)

        next_available_email_provider = create_email_provider(
            name='Next available email provider', hourly_limit=30, pos=5, available=True)

        with requests_mock.mock() as r:
            r.post(next_available_email_provider.api_url, text='OK')
            resp = send_email('someone@example.com', 'test subject', 'test message')

            assert resp == (200, next_available_email_provider.id)

    def it_doesnt_send_email_if_disabled(self, mocker, mock_config_disabled):
        mock_logger = mocker.patch('app.comms.email.current_app.logger.info')

        send_email('someone@example.com', 'test subject', 'test message')

        assert mock_logger.call_args == call("Emails disabled, unset EMAIL_DISABLED env var to re-enable")


class WhenGettingEmailData:

    def it_gets_basic_email_data(self):
        data_map = {
            "from": "from",
            "to": "to",
            "subject": "subject",
            "message": "message"
        }

        data = get_email_data(
            data_map, "test@example.com", "Test email", "Some test message", "noone@example.com", "No one"
        )
        assert data == {
            'to': 'test@example.com',
            'message': 'Some test message',
            'from': 'noone@example.com',
            'subject': 'Test email'
        }

    def it_gets_complex_email_data(self):
        data_map = {
            "from": "from,email",
            "from_name": "from,name",
            "to": "to,[email]",
            "subject": "subject",
            "message": "html"
        }

        data = get_email_data(
            data_map, "test@example.com", "Test email", "Some test message", "noone@example.com", "No one"
        )
        assert data == {
            'to': [
                {'email': 'test@example.com'}
            ],
            'html': 'Some test message',
            'from': {'email': 'noone@example.com', 'name': 'No one'},
            'subject': 'Test email'
        }

    def it_gets_complex_email_data_with_list(self):
        data_map = {
            "from": "from,email",
            "from_name": "from,name",
            "to": "to,[email]",
            "subject": "subject",
            "message": "html"
        }

        data = get_email_data(
            data_map, ["test@example.com", "test1@example.com"],
            "Test email", "Some test message", "noone@example.com", "No one"
        )

        assert data == {
            'to': [
                {'email': 'test@example.com'},
                {'email': 'test1@example.com'}
            ],
            'html': 'Some test message',
            'from': {'email': 'noone@example.com', 'name': 'No one'},
            'subject': 'Test email'
        }


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

    @pytest.mark.parametrize('topics', [
        "Philosophy- test 1\nCulture- test 2\nArt- test 3",
        "Philosophy test 1\nCulture test 2\nArt test 3",
        "Philosophy: test 1\nCulture- test 2\nArt test 3",
    ])
    def it_shows_divider_error(self, mocker, db_session, sample_magazine, topics):
        mock_render_template = mocker.patch('app.comms.email.render_template')
        sample_magazine.topics = topics
        get_email_html(MAGAZINE, magazine_id=sample_magazine.id)

        args, kwargs = mock_render_template.call_args
        assert args[0] == 'emails/magazine.html'
        assert kwargs['topics'] == [
            {'description': 'Use : as divider between topic header and sub-header', 'title': 'Missing divider'},
            {'description': topics, 'title': 'Topics'}
        ]
