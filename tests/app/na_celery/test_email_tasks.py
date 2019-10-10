from bs4 import BeautifulSoup
from flask import current_app
from freezegun import freeze_time

from app.na_celery.email_tasks import send_emails, send_periodic_emails
from app.comms.encryption import decrypt, get_tokens
from app.models import APPROVED

from tests.db import create_email, create_member


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

    def it_only_sends_to_3_emails_if_not_live_environment(self, mocker, db, db_session, sample_email, sample_member):
        member_1 = create_member(name='Test 1', email='test1@example.com')
        member_2 = create_member(name='Test 2', email='test2@example.com')
        member_3 = create_member(name='Test 3', email='test3@example.com')

        mock_send_email = mocker.patch('app.na_celery.email_tasks.send_email', return_value=200)
        send_emails(sample_email.id)

        assert mock_send_email.call_count == 3
        assert mock_send_email.call_args_list[0][0][0] == sample_member.email
        assert mock_send_email.call_args_list[1][0][0] == member_1.email
        assert mock_send_email.call_args_list[2][0][0] == member_2.email

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

    def it_sends_an_email_to_members_up_to_email_limit(self):
        pass

    def it_does_not_send_an_email_if_not_between_start_and_expiry(self):
        pass

    def it_sends_email_with_correct_template(self):
        pass
