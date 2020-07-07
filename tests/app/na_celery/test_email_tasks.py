from bs4 import BeautifulSoup
from flask import current_app
from freezegun import freeze_time
import pytest

from app.na_celery.email_tasks import send_emails, send_periodic_emails
from app.comms.encryption import decrypt, get_tokens
from app.errors import InvalidRequest
from app.models import APPROVED

from tests.db import create_email, create_member, create_email_to_member, create_email_provider


class WhenProcessingSendEmailsTask:

    def it_calls_send_email_to_task(self, mocker, db, db_session, sample_email, sample_member):
        mock_send_email = mocker.patch('app.na_celery.email_tasks.send_email', return_value=200)
        send_emails(sample_email.id)

        assert mock_send_email.call_args[0][0] == sample_member.email
        assert mock_send_email.call_args[0][1] == 'workshop: test title'
        page = BeautifulSoup(mock_send_email.call_args[0][2], 'html.parser')
        assert 'http://frontend-test/member/unsubscribe' in str(page)

        unsubcode = page.select_one('#unsublink')['href'].split('/')[-1]
        tokens = get_tokens(decrypt(unsubcode, current_app.config['EMAIL_UNSUB_SALT']))
        assert tokens[current_app.config['EMAIL_TOKENS']['member_id']] == str(sample_member.id)
        assert sample_email.serialize()['emails_sent_counts'] == {
            'success': 1,
            'failed': 0,
            'total_active_members': 1
        }

    def it_only_sends_to_3_emails_if_not_live_environment(self, mocker, db_session, sample_email, sample_member):
        mocker.patch.dict('app.application.config', {
            'ENVIRONMENT': 'test',
            'EMAIL_RESTRICT': None
        })

        member_1 = create_member(name='Test 1', email='test1@example.com')
        member_2 = create_member(name='Test 2', email='test2@example.com')
        create_member(name='Test 3', email='test3@example.com')

        mock_send_email = mocker.patch('app.na_celery.email_tasks.send_email', return_value=200)
        send_emails(sample_email.id)

        assert mock_send_email.call_count == 3
        assert mock_send_email.call_args_list[0][0][0] == sample_member.email
        assert mock_send_email.call_args_list[1][0][0] == member_1.email
        assert mock_send_email.call_args_list[2][0][0] == member_2.email
        assert sample_email.serialize()['emails_sent_counts'] == {
            'success': 3,
            'failed': 0,
            'total_active_members': 4
        }

    def it_only_sends_to_1_emails_if_restrict_email(self, mocker, db, db_session, sample_email, sample_member):
        mocker.patch.dict('app.application.config', {
            'ENVIRONMENT': 'test',
            'EMAIL_RESTRICT': 1
        })

        create_member(name='Test 1', email='test1@example.com')

        mock_send_email = mocker.patch('app.na_celery.email_tasks.send_email', return_value=200)
        send_emails(sample_email.id)

        assert mock_send_email.call_count == 1
        assert mock_send_email.call_args_list[0][0][0] == sample_member.email

    def it_only_sends_to_unsent_members_and_shows_failed_stat(
        self, mocker, db, db_session, sample_email, sample_member
    ):
        mocker.patch.dict('app.application.config', {
            'ENVIRONMENT': 'test',
            'EMAIL_RESTRICT': None
        })

        member_1 = create_member(name='Test 1', email='test1@example.com')
        member_2 = create_member(name='Test 2', email='test2@example.com')
        create_member(name='Test 2', email='test3@example.com', active=False)

        create_email_to_member(sample_email.id, sample_member.id, status_code=500)

        mock_send_email = mocker.patch('app.na_celery.email_tasks.send_email', return_value=200)
        send_emails(sample_email.id)

        assert mock_send_email.call_count == 2
        assert mock_send_email.call_args_list[0][0][0] == member_1.email
        assert mock_send_email.call_args_list[1][0][0] == member_2.email
        assert sample_email.serialize()['emails_sent_counts'] == {
            'success': 2,
            'failed': 1,
            'total_active_members': 3
        }

    @freeze_time("2019-06-03T10:00:00")
    def it_only_sends_approved_emails(self, mocker, db, db_session, sample_email, sample_member):
        mock_send_emails = mocker.patch('app.na_celery.email_tasks.send_emails')
        create_email(send_starts_at='2019-06-07', created_at='2019-06-01', send_after='2019-06-07 9:00')
        create_email(send_starts_at='2019-08-08', created_at='2019-06-01', send_after='2019-07-14 9:00')

        approved_email = create_email(
            send_starts_at='2019-06-02',
            created_at='2019-06-01',
            send_after='2019-06-03 9:00',
            email_state=APPROVED
        )
        send_periodic_emails()

        assert mock_send_emails.call_count == 1
        assert mock_send_emails.call_args_list[0][0][0] == approved_email.id

    def it_sends_an_email_to_members_up_to_email_limit(self, mocker, db_session, sample_email, sample_member):
        mocker.patch.dict('app.application.config', {
            'ENVIRONMENT': 'live',
            'EMAIL_RESTRICT': None
        })
        create_email_provider(daily_limit=2)

        member_1 = create_member(name='Test 1', email='test1@example.com')
        create_member(name='Test 2', email='test2@example.com')

        mock_send_email = mocker.patch('app.na_celery.email_tasks.send_email', return_value=200)
        send_emails(sample_email.id)

        assert mock_send_email.call_count == 2
        assert mock_send_email.call_args_list[0][0][0] == sample_member.email
        assert mock_send_email.call_args_list[1][0][0] == member_1.email
        assert sample_email.serialize()['emails_sent_counts'] == {
            'success': 2,
            'failed': 0,
            'total_active_members': 3
        }

    def it_logs_429_status_code_response(self, mocker, db_session, sample_email, sample_member):
        mocker.patch(
            'app.na_celery.email_tasks.send_email',
            side_effect=InvalidRequest('Daily limit reached', 429)
        )
        mock_logger_error = mocker.patch('app.na_celery.email_tasks.current_app.logger.error')
        send_emails(sample_email.id)
        assert mock_logger_error.called
        args = mock_logger_error.call_args[0]
        assert args[0] == 'Email limit reached: %r'
        assert args[1] == 'Daily limit reached'

    def it_reraises_if_not_429_status_code_response(self, mocker, db_session, sample_email, sample_member):
        mocker.patch(
            'app.na_celery.email_tasks.send_email',
            side_effect=InvalidRequest('Unknown', 400)
        )

        with pytest.raises(InvalidRequest):
            send_emails(sample_email.id)

    def it_does_not_send_an_email_if_not_between_start_and_expiry(self):
        pass

    def it_sends_email_with_correct_template(self):
        pass
