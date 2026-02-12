from bs4 import BeautifulSoup
from datetime import datetime
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask import current_app
from freezegun import freeze_time
import json
from mock import call
import pytest
from urllib.parse import parse_qs

from app.na_celery.email_tasks import send_emails, send_periodic_emails, send_missing_confirmation_emails
from app.comms.encryption import decrypt, get_tokens
from app.errors import InvalidRequest
from app.models import APPROVED, DRAFT, TICKET_STATUS_UNUSED, Email, Magazine, EmailToMember, MAGAZINE
from tests.app.routes.orders.test_rest import sample_ipns

from tests.db import (
    create_email, create_event, create_event_date, create_member, create_email_to_member,
    create_email_provider, create_order, create_ticket
)


class WhenProcessingSendEmailsTask:

    def it_calls_send_email_to_task(self, mocker, db, db_session, sample_email, sample_member, sample_email_provider):
        mock_send_email = mocker.patch(
            'app.na_celery.email_tasks.send_email', return_value=(200, sample_email_provider.id))
        mocker.patch('requests.post')
        send_emails(sample_email.id)

        assert mock_send_email.call_args[0][0] == sample_member.email
        assert mock_send_email.call_args[0][1] == 'workshop: test_title'
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

    @freeze_time("2020-10-09T19:00:00")
    def it_only_sends_to_3_emails_if_not_live_environment(
        self, mocker, db_session, sample_email, sample_member, sample_email_provider
    ):
        mocker.patch.dict('app.application.config', {
            'ENVIRONMENT': 'test',
            'EMAIL_RESTRICT': None
        })

        member_1 = create_member(name='Test 1', email='test1@example.com')
        member_2 = create_member(name='Test 2', email='test2@example.com')
        create_member(name='Test 3', email='test3@example.com')

        mock_send_email = mocker.patch(
            'app.na_celery.email_tasks.send_email', return_value=(200, sample_email_provider.id))
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

        emails_to_members = EmailToMember.query.all()
        assert len(emails_to_members) == 3
        assert emails_to_members[0].email_provider_id == sample_email_provider.id
        assert emails_to_members[0].created_at == datetime.strptime("2020-10-09 19:00", "%Y-%m-%d %H:%M")

    def it_only_sends_to_1_emails_if_restrict_email(
        self, mocker, db, db_session, sample_email, sample_member, sample_email_provider
    ):
        mocker.patch.dict('app.application.config', {
            'ENVIRONMENT': 'test',
            'EMAIL_RESTRICT': 1
        })

        create_member(name='Test 1', email='test1@example.com')

        mock_send_email = mocker.patch(
            'app.na_celery.email_tasks.send_email', return_value=(200, sample_email_provider.id)
        )
        send_emails(sample_email.id)

        assert mock_send_email.call_count == 1
        assert mock_send_email.call_args_list[0][0][0] == sample_member.email

    def it_only_sends_to_first_member_if_email_test_and_doesnt_record_it(
        self, mocker, db, db_session, sample_email, sample_member, sample_email_provider
    ):
        mocker.patch.dict('app.application.config', {
            'ENVIRONMENT': 'test',
            'EMAIL_TEST': 1
        })
        mock_record_member_email = mocker.patch('app.na_celery.email_tasks.dao_add_member_sent_to_email')

        create_member(name='Test 1', email='test1@example.com')

        mock_send_email = mocker.patch(
            'app.na_celery.email_tasks.send_email', return_value=(200, sample_email_provider.id)
        )
        send_emails(sample_email.id)

        assert mock_send_email.call_count == 1
        assert mock_send_email.call_args_list[0][0][0] == sample_member.email
        assert not mock_record_member_email.called

    def it_doesnt_send_unapproved_emails(self, mocker, db, db_session, sample_email, sample_member):
        mocker.patch.dict('app.application.config', {
            'ENVIRONMENT': 'test',
            'EMAIL_RESTRICT': 1
        })
        sample_email.email_state = DRAFT

        create_member(name='Test 1', email='test1@example.com')

        mock_send_email = mocker.patch('app.na_celery.email_tasks.send_email', return_value=200)
        mock_logger = mocker.patch('app.na_celery.email_tasks.current_app.logger.info')
        send_emails(sample_email.id)

        assert not mock_send_email.called
        assert mock_logger.called

    def it_only_sends_to_unsent_members_and_shows_failed_stat(
        self, mocker, db, db_session, sample_email, sample_member, sample_email_provider
    ):
        mocker.patch.dict('app.application.config', {
            'ENVIRONMENT': 'test',
            'EMAIL_RESTRICT': None
        })

        member_1 = create_member(name='Test 1', email='test1@example.com')
        member_2 = create_member(name='Test 2', email='test2@example.com')
        create_member(name='Test 2', email='test3@example.com', active=False)

        create_email_to_member(sample_email.id, sample_member.id, status_code=500)

        # respond with 201 on 2nd call
        mock_send_email = mocker.patch(
            'app.na_celery.email_tasks.send_email',
            side_effect=[(200, sample_email_provider.id), (201, sample_email_provider.id)]
        )
        send_emails(sample_email.id)

        assert mock_send_email.call_count == 2

        emails_sent = []
        for i in range(2):
            emails_sent.append(mock_send_email.call_args_list[i][0][0])

        assert member_1.email in emails_sent
        assert member_2.email in emails_sent
        assert sample_email.serialize()['emails_sent_counts'] == {
            'success': 2,
            'failed': 1,
            'total_active_members': 3
        }

    @freeze_time("2019-06-03T10:00:00")
    def it_only_sends_approved_emails_periodically(self, mocker, db, db_session, sample_email, sample_member):
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

    @freeze_time("2019-06-03T10:00:00")
    def it_doesnt_sends_approved_emails_periodically_if_has_child_email(
        self, mocker, db, db_session, sample_email, sample_member
    ):
        mock_send_emails = mocker.patch('app.na_celery.email_tasks.send_emails')

        approved_email_with_chiild_email = create_email(
            send_starts_at='2019-06-02',
            created_at='2019-06-01',
            send_after='2019-06-03 9:00',
            email_state=APPROVED
        )
        approved_email = create_email(
            send_starts_at='2019-06-02',
            created_at='2019-06-01',
            send_after='2019-06-03 9:00',
            email_state=APPROVED,
            parent_email_id=approved_email_with_chiild_email.id
        )

        approved_email_without_parent = create_email(
            send_starts_at='2019-06-02',
            created_at='2019-06-01',
            send_after='2019-06-03 9:00',
            email_state=APPROVED
        )

        send_periodic_emails()

        assert mock_send_emails.call_count == 2
        assert mock_send_emails.call_args_list[0][0][0] == approved_email.id
        assert mock_send_emails.call_args_list[1][0][0] == approved_email_without_parent.id

    @pytest.mark.parametrize('now', [
        "2020-09-05T23:00:01",
        "2020-09-05T06:00:00",
    ])
    def it_doesnt_send_email_out_of_hours(self, mocker, db_session, sample_email, sample_member, now):
        mock_get_emails = mocker.patch('app.na_celery.email_tasks.dao_get_approved_emails_for_sending')

        create_email(
            send_starts_at='2020-06-02',
            created_at='2020-06-01',
            send_after='2020-06-03 9:00',
            email_state=APPROVED,
            email_type=MAGAZINE
        )
        with freeze_time(now):
            send_periodic_emails()

        assert not mock_get_emails.called

    @pytest.mark.parametrize('now', [
        "2020-09-05T23:00:01",
        "2020-09-05T06:00:00",
    ])
    def it_sends_emails_anytime(self, mocker, db_session, sample_email, sample_member, now):
        mocker.patch.dict('app.application.config', {
            'ENVIRONMENT': 'test',
            'EMAIL_RESTRICT': None,
            'EMAIL_ANYTIME': True
        })
        mock_send_emails = mocker.patch('app.na_celery.email_tasks.send_emails')

        event_date = create_event_date(event_datetime='2020-09-20 19:00')
        event = create_event(event_dates=[event_date])
        create_email(
            send_starts_at='2020-09-02',
            created_at='2020-09-01',
            send_after='2020-09-03 8:00',
            expires=None,
            email_state=APPROVED,
            old_event_id=None,
            event_id=event.id
        )

        with freeze_time(now):
            send_periodic_emails()

        assert mock_send_emails.called

    @pytest.mark.parametrize('now', [
        "2020-09-05T20:59:01",  # UTC london time at 21:59
        "2020-09-05T08:00:01",
    ])
    def it_sends_email_in_hours(self, mocker, db_session, sample_email, sample_member, now):
        mock_send_emails = mocker.patch('app.na_celery.email_tasks.send_emails')
        event_date = create_event_date(event_datetime='2020-09-20 19:00')
        event = create_event(event_dates=[event_date])
        create_email(
            send_starts_at='2020-09-02',
            created_at='2020-09-01',
            send_after='2020-09-03 8:00',
            expires=None,
            email_state=APPROVED,
            old_event_id=None,
            event_id=event.id
        )
        with freeze_time(now):
            send_periodic_emails()

        assert mock_send_emails.called

    @pytest.mark.parametrize('monthly,daily,hourly,minute,expected_limit', [
        (2, 0, 0, 0, 2),
        (0, 2, 0, 0, 2),
        (0, 0, 2, 0, 2),
        (0, 0, 0, 2, 1),  # minute limits are ignored in email task, use config EMAIL_LIMIT
    ])
    def it_sends_an_email_to_members_up_to_email_limit(
        self, mocker, db_session, sample_email,
        monthly, daily, hourly, minute, expected_limit
    ):
        mocker.patch.dict('app.application.config', {
            'ENVIRONMENT': 'live',
            'EMAIL_RESTRICT': None,
            'EMAIL_LIMIT': 1
        })
        mocker.patch('requests.post')
        email_provider = create_email_provider(
            monthly_limit=monthly,
            daily_limit=daily,
            hourly_limit=hourly,
            minute_limit=minute
        )

        member_0 = create_member(name='Sue Green', email='sue@example.com')
        member_1 = create_member(name='Test 1', email='test1@example.com')
        create_member(name='Test 2', email='test2@example.com')
        # member created after email expired not counted
        create_member(name='Test 3', email='test3@example.com', created_at='2019-08-09T19:00:00')

        mock_send_email = mocker.patch(
            'app.na_celery.email_tasks.send_email', return_value=(200, email_provider.id))
        send_emails(sample_email.id)

        assert mock_send_email.call_count == expected_limit
        assert mock_send_email.call_args_list[0][0][0] == member_0.email
        if expected_limit > 1:
            assert mock_send_email.call_args_list[1][0][0] == member_1.email
        assert sample_email.serialize()['emails_sent_counts'] == {
            'success': expected_limit,
            'failed': 0,
            'total_active_members': 3
        }

    def it_sends_a_magazine_email(
        self, mocker, db_session, sample_magazine_email, sample_member, sample_email_provider
    ):
        mocker.patch.dict('app.application.config', {
            'ENVIRONMENT': 'test',
            'EMAIL_RESTRICT': 1
        })

        create_member(name='Test 1', email='test1@example.com')

        mock_send_email = mocker.patch(
            'app.na_celery.email_tasks.send_email', return_value=(200, str(sample_email_provider.id)))
        send_emails(sample_magazine_email.id)

        magazine = Magazine.query.filter_by(id=sample_magazine_email.magazine_id).first()
        assert magazine

        assert magazine.title in mock_send_email.call_args_list[0][0][1]
        assert magazine.filename in mock_send_email.call_args_list[0][0][2]
        assert mock_send_email.call_count == 1
        assert mock_send_email.call_args_list[0][0][0] == sample_member.email

    def it_sends_a_basic_email(
        self, mocker, db_session, sample_basic_email, sample_member, sample_email_provider
    ):
        mocker.patch.dict('app.application.config', {
            'ENVIRONMENT': 'test',
            'EMAIL_RESTRICT': 1
        })

        create_member(name='Test 1', email='test1@example.com')

        mock_send_email = mocker.patch(
            'app.na_celery.email_tasks.send_email', return_value=(200, str(sample_email_provider.id)))
        send_emails(sample_basic_email.id)

        basic = Email.query.filter_by(id=sample_basic_email.id).first()
        assert basic

        assert basic.subject in mock_send_email.call_args_list[0][0][1]
        assert basic.extra_txt in mock_send_email.call_args_list[0][0][2]
        assert mock_send_email.call_count == 1
        assert mock_send_email.call_args_list[0][0][0] == sample_member.email

    def it_logs_429_status_code_response(self, mocker, db_session, sample_email, sample_member):
        mocker.patch(
            'app.na_celery.email_tasks.send_email',
            side_effect=InvalidRequest('Minute limit reached', 429)
        )
        mock_logger_error = mocker.patch('app.na_celery.email_tasks.current_app.logger.error')
        mock_send_periodic_task = mocker.patch('app.na_celery.email_tasks.send_periodic_emails.apply_async')
        with pytest.raises(expected_exception=InvalidRequest):
            send_emails(sample_email.id)
        assert mock_logger_error.called
        args = mock_logger_error.call_args[0]
        assert args[0] == 'Email limit reached: %r'
        assert args[1] == 'Minute limit reached'
        assert mock_send_periodic_task.called
        assert mock_send_periodic_task.call_args == call(countdown=60)

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


class WhenProcessingSendMissingConfirmationEmailsTask:

    @freeze_time("2022-11-24T09:00:00")
    def it_sends_missing_confirmation_emails(
        self, db, db_session, mocker, sample_email_provider, sample_event_with_dates, mock_storage
    ):
        txn_ids = ['112233', '112244']
        txn_types = ['cart', 'cart']
        num_tickets = [1, 2]

        create_order(created_at='2022-11-21T19:00:00', txn_id='111')  # more than 2 days before so ignore

        for i in range(len(txn_ids)):
            sample_ipns[i] = sample_ipns[i].format(
                id=sample_event_with_dates.id, txn_id=txn_ids[i], txn_type=txn_types[i])

        order = create_order(
            created_at='2022-11-22T19:00:00', txn_id='112233', params=json.dumps(parse_qs(sample_ipns[0]))
        )  # 2 days before
        order2 = create_order(
            created_at='2022-11-24T08:00:00', txn_id='112244', params=json.dumps(parse_qs(sample_ipns[1]))
        )  # on the day of the task
        create_order(
            created_at='2022-11-24T09:00:00', txn_id='112255', params=json.dumps(parse_qs(sample_ipns[2])),
            email_status="202"
        )  # ignored as email status set

        mock_send_email = mocker.patch(
            'app.routes.orders.rest.send_email', return_value=(200, str(sample_email_provider.id))
        )

        mock_url_for = mocker.patch(
            'app.routes.orders.rest.url_for', return_value="/orders/ticket/ticket_id"
        )
        send_missing_confirmation_emails()

        assert mock_send_email.call_count == 2
        assert str(order.txn_id) in mock_send_email.call_args_list[0][0][2]
        assert str(order2.txn_id) in mock_send_email.call_args_list[1][0][2]

    @freeze_time("2022-11-24T09:00:00")
    def it_sets_email_status_500_on_missing_email_status_after_retry(
        self, db, db_session, mocker, sample_email_provider, sample_event_with_dates, mock_storage
    ):
        txn_ids = ['112233']
        txn_types = ['cart']
        num_tickets = [1]

        sample_ipns[0] = sample_ipns[0].format(
            id=sample_event_with_dates.id, txn_id=txn_ids[0], txn_type=txn_types[0])

        order = create_order(
            created_at='2022-11-22T19:00:00', txn_id='112233', params=json.dumps(parse_qs(sample_ipns[0]))
        )

        mock_send_email = mocker.patch(
            'app.routes.orders.rest.send_email', return_value=(200, str(sample_email_provider.id))
        )

        mock_replay_ipn = mocker.patch(
            'app.na_celery.email_tasks._replay_paypal_ipn', return_value=None
        )

        send_missing_confirmation_emails()

        assert mock_send_email.call_count == 0
        assert order.email_status == "500"
