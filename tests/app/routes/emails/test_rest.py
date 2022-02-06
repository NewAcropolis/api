from datetime import datetime, timedelta
from freezegun import freeze_time
from freezegun.api import FakeDatetime
from mock import Mock, call
import pytest
import six.moves.urllib as urllib
from sqlalchemy.orm.exc import NoResultFound

from bs4 import BeautifulSoup
from flask import json, url_for

from app.models import (
    ANON_REMINDER, ANNOUNCEMENT, EVENT, MAGAZINE, MANAGED_EMAIL_TYPES, APPROVED, READY, REJECTED, Email
)
from app.dao.emails_dao import dao_add_member_sent_to_email
from tests.conftest import create_authorization_header, request, TEST_ADMIN_USER
from tests.db import create_email, create_event, create_event_date, create_magazine, create_member


@pytest.fixture
def sample_old_emails():
    magazine = create_magazine()

    return [
        {
            "id": "1",
            "eventid": "-1",
            "eventdetails": "New Acropolis Newsletter Issue 1",
            "extratxt": "<a href='http://www.example.org/download.php?<member>&id=1'><img title="
            "'Click to download Issue 1' src='http://www.example.org/images/NA_Newsletter_Issue_1.pdf'></a>",
            "replaceAll": "n",
            "timestamp": "2019-01-01 10:00:00",
            "Title": "",
            "ImageFilename": "",
            "Status": "new",
            "limit_sending": "0"
        },
        {
            "id": "2",
            "eventid": "1",
            "magazine_id": str(magazine.id),
            "eventdetails": "",
            "extratxt": "",
            "replaceAll": "n",
            "timestamp": "2019-02-01 11:00:00",
        },
        {
            "id": "3",
            "eventid": "-2",
            "eventdetails": "Some announcement",
            "extratxt": "",
            "replaceAll": "n",
            "timestamp": "2019-03-01 11:00:00",
        },
        {
            "id": "4",
            "eventid": "-2",
            "eventdetails": "Last chance to verify your email to restart your subscription",
            "extratxt": "",
            "replaceAll": "n",
            "timestamp": "2019-03-01 11:00:00",
        }
    ]


class WhenGettingEmailTypes:
    def it_returns_email_types(self, client):
        response = client.get(
            url_for('emails.get_email_types'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        json_email_types = json.loads(response.get_data(as_text=True))

        assert set(MANAGED_EMAIL_TYPES) == set([email_type['type'] for email_type in json_email_types])


class WhenGettingFutureEmails:
    @freeze_time("2019-07-10T10:00:00")
    def it_returns_future_emails(self, client, db, db_session):
        event = create_event(title='Event 1')
        event_2 = create_event(title='Event 2')
        event_3 = create_event(title='Event 3')
        past_event = create_event(title='Past event')

        event_date = create_event_date(event_id=str(event.id), event_datetime='2019-07-20 19:00')
        event_date_2 = create_event_date(event_id=str(event_2.id), event_datetime='2019-07-13 19:00')
        event_date_3 = create_event_date(event_id=str(event_3.id), event_datetime='2019-08-13 19:00')
        past_event_date = create_event_date(event_id=str(past_event.id), event_datetime='2019-06-13 19:00')

        future_email = create_email(
            event_id=str(event.id), created_at='2019-07-01 11:00', send_starts_at='2019-07-10', expires='2019-07-20')
        future_email_2 = create_email(
            event_id=str(event_2.id), created_at='2019-07-01 11:00', send_starts_at='2019-07-01', expires='2019-07-12')
        future_email_3 = create_email(
            event_id=str(event_3.id), created_at='2019-07-01 11:00', send_starts_at='2019-08-01', expires='2019-08-12')
        # email below will be ignored as its in the past
        create_email(
            event_id=str(past_event.id),
            created_at='2019-06-01 11:00',
            send_starts_at='2019-06-01',
            expires='2019-06-12')

        response = client.get(
            url_for('emails.get_future_emails'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        json_future_emails = json.loads(response.get_data(as_text=True))

        assert len(json_future_emails) == 3
        assert json_future_emails[0] == future_email.serialize()
        assert json_future_emails[1] == future_email_2.serialize()
        assert json_future_emails[2] == future_email_3.serialize()


class WhenGettingLatestEmails:
    @freeze_time("2019-07-10T10:00:00")
    def it_returns_latest_emails(self, client, db, db_session):
        event = create_event(title='Event 1')
        event_2 = create_event(title='Event 2')
        event_3 = create_event(title='Event 3')
        past_event = create_event(title='Past event')

        event_date = create_event_date(event_id=str(event.id), event_datetime='2019-07-20 19:00')
        event_date_2 = create_event_date(event_id=str(event_2.id), event_datetime='2019-07-13 19:00')
        event_date_3 = create_event_date(event_id=str(event_3.id), event_datetime='2019-08-13 19:00')
        past_event_date = create_event_date(event_id=str(past_event.id), event_datetime='2019-06-13 19:00')

        future_email = create_email(
            event_id=str(event.id), created_at='2019-07-01 11:00', send_starts_at='2019-07-10', expires='2019-07-20')
        future_email_2 = create_email(
            event_id=str(event_2.id), created_at='2019-07-02 11:00', send_starts_at='2019-07-01', expires='2019-07-12')
        future_email_3 = create_email(
            event_id=str(event_3.id), created_at='2019-07-03 11:00', send_starts_at='2019-08-01', expires='2019-08-12')
        past_email = create_email(
            event_id=str(past_event.id),
            created_at='2019-06-01 11:00',
            send_starts_at='2019-06-01',
            expires='2019-06-12')

        response = client.get(
            url_for('emails.get_latest_emails'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        json_latest_emails = json.loads(response.get_data(as_text=True))

        assert len(json_latest_emails) == 4
        assert json_latest_emails[0] == future_email_3.serialize()
        assert json_latest_emails[1] == future_email_2.serialize()
        assert json_latest_emails[2] == future_email.serialize()
        assert json_latest_emails[3] == past_email.serialize()


class WhenGettingApprovedEmails:
    @freeze_time("2019-07-11T10:00:00")
    def it_returns_approved_emails(self, client, db, db_session):
        event = create_event(title='Event 1')
        event_2 = create_event(title='Event 2')

        event_date = create_event_date(event_id=str(event.id), event_datetime='2019-07-20 19:00')
        event_date_2 = create_event_date(event_id=str(event_2.id), event_datetime='2019-07-13 19:00')

        approved_email = create_email(
            event_id=str(event.id), created_at='2019-07-01 11:00', send_starts_at='2019-07-10',
            send_after='2019-07-01 11:00', expires='2019-07-20', email_state='approved')
        create_email(
            event_id=str(event_2.id), created_at='2019-07-02 11:00', send_starts_at='2019-07-01', expires='2019-07-12')

        response = client.get(
            url_for('emails.get_approved_emails'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        json_latest_emails = json.loads(response.get_data(as_text=True))

        assert len(json_latest_emails) == 1
        assert json_latest_emails[0] == approved_email.serialize()


class WhenPostingImportingEmails:
    def it_creates_emails_for_imported_emails(
        self, client, db_session, sample_old_emails, sample_event_with_dates
    ):
        response = client.post(
            url_for('emails.import_emails'),
            data=json.dumps(sample_old_emails),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_emails = json.loads(response.get_data(as_text=True))['emails']
        email_types = [MAGAZINE, EVENT, ANNOUNCEMENT, ANON_REMINDER]
        assert len(json_emails) == len(sample_old_emails)

        for i in range(0, len(sample_old_emails)):
            if json_emails[i]['email_type'] == EVENT:
                assert json_emails[i]['event_id'] == str(sample_event_with_dates.id)
            assert json_emails[i]['email_type'] == email_types[i]
            assert json_emails[i]['created_at'] == sample_old_emails[i]['timestamp'][:-3]
            assert json_emails[i]['extra_txt'] == sample_old_emails[i]['extratxt']
            assert json_emails[i]['details'] == sample_old_emails[i]['eventdetails']
            assert str(json_emails[i]['old_id']) == sample_old_emails[i]['id']
            assert str(json_emails[i]['old_event_id']) == sample_old_emails[i]['eventid']
            assert json_emails[i]['replace_all'] == (True if sample_old_emails[i]['replaceAll'] == 'y' else False)
            assert json_emails[i]['send_starts_at'] == sample_old_emails[i]['timestamp'].split(' ')[0]
            expiry = (datetime.strptime(sample_old_emails[i]['timestamp'].split(' ')[0], "%Y-%m-%d") +
                      timedelta(weeks=2)).strftime("%Y-%m-%d") \
                if email_types[i] != EVENT else sample_event_with_dates.get_last_event_date()
            assert json_emails[i]['expires'] == expiry

    def it_doesnt_create_email_for_imported_emails_already_imported(
        self, client, db_session, sample_old_emails, sample_event
    ):
        create_email()  # email with old_id=1
        response = client.post(
            url_for('emails.import_emails'),
            data=json.dumps(sample_old_emails),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        json_emails = json_resp['emails']
        email_types = [EVENT, ANNOUNCEMENT, ANON_REMINDER]
        assert len(json_emails) == len(sample_old_emails) - 1
        for i in range(0, len(sample_old_emails) - 1):
            assert json_emails[i]['email_type'] == email_types[i]
            assert json_emails[i]['created_at'] == sample_old_emails[i + 1]['timestamp'][:-3]
            assert json_emails[i]['extra_txt'] == sample_old_emails[i + 1]['extratxt']
            assert json_emails[i]['details'] == sample_old_emails[i + 1]['eventdetails']
            assert str(json_emails[i]['old_id']) == sample_old_emails[i + 1]['id']
            assert str(json_emails[i]['old_event_id']) == sample_old_emails[i + 1]['eventid']
            assert json_emails[i]['replace_all'] == (True if sample_old_emails[i + 1]['replaceAll'] == 'y' else False)
        json_errors = json_resp['errors']
        assert json_errors == ['email already exists: 1']

    def it_doesnt_create_email_for_imported_event_email_without_event(
        self, client, db_session, sample_old_emails
    ):
        response = client.post(
            url_for('emails.import_emails'),
            data=json.dumps(sample_old_emails),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_resp = json.loads(response.get_data(as_text=True))
        json_emails = json_resp['emails']
        email_types = [MAGAZINE, ANNOUNCEMENT, ANON_REMINDER]
        assert len(json_emails) == len(sample_old_emails) - 1
        offset = 0
        for i in range(0, len(sample_old_emails) - 1):
            if i == 1:
                offset = 1  # skip event email as shouldnt be created
            assert json_emails[i]['email_type'] == email_types[i]
            assert json_emails[i]['created_at'] == sample_old_emails[i + offset]['timestamp'][:-3]
            assert json_emails[i]['extra_txt'] == sample_old_emails[i + offset]['extratxt']
            assert json_emails[i]['details'] == sample_old_emails[i + offset]['eventdetails']
            assert str(json_emails[i]['old_id']) == sample_old_emails[i + offset]['id']
            assert str(json_emails[i]['old_event_id']) == sample_old_emails[i + offset]['eventid']
            assert json_emails[i]['replace_all'] == (
                True if sample_old_emails[i + offset]['replaceAll'] == 'y' else False)
        json_errors = json.loads(json_resp['errors'][0][len('event not found: '):].replace('\'', '"'))
        assert json_resp['errors'][0].startswith('event not found: ')
        assert json_errors == sample_old_emails[1]


class WhenPreviewingEmails:

    def it_returns_an_email_preview(self, client, db_session, sample_event_with_dates):
        data = {
            "event_id": str(sample_event_with_dates.id),
            "details": "<div>Some additional details</div>",
            "extra_txt": "<div>Some more information about the event</div>",
            "replace_all": False,
            "email_type": "event"
        }

        encoded_data = urllib.parse.quote(json.dumps(data))

        html = request(
            url_for('emails.email_preview', data=encoded_data),
            client.get,
            headers=[('Content-Type', 'application/json'), create_authorization_header()])

        assert html.soup.select_one('h3').text.strip() == 'Mon 1, Tues 2 of January - 7 PM'
        assert html.soup.select_one('.event_text h4').text == 'WORKSHOP: test_title'

        assert data['details'] in str(html.soup.select_one('.event_text'))
        assert data['extra_txt'] in str(html.soup.select_one('.event_text'))


class WhenPostingCreateEmail:

    def it_creates_an_event_email(self, mocker, client, db_session, sample_event_with_dates):
        data = {
            "event_id": str(sample_event_with_dates.id),
            "details": "<div>Some additional details</div>",
            "extra_txt": "<div>Some more information about the event</div>",
            "replace_all": False,
            "email_type": "event"
        }

        response = client.post(
            url_for('emails.create_email'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        json_resp = json.loads(response.get_data(as_text=True))

        assert json_resp['email_type'] == 'event'
        assert not json_resp['old_id']
        assert json_resp['event_id'] == str(sample_event_with_dates.id)
        assert not json_resp['old_event_id']
        assert json_resp['extra_txt'] == '<div>Some more information about the event</div>'
        assert json_resp['details'] == '<div>Some additional details</div>'
        assert not json_resp['replace_all']

        emails = Email.query.all()

        assert len(emails) == 1
        assert emails[0].email_type == 'event'
        assert emails[0].event_id == sample_event_with_dates.id

    def it_does_not_create_an_event_email_if_no_event_matches(self, client, db_session, sample_uuid):
        data = {
            "event_id": sample_uuid,
            "details": "<div>Some additional details</div>",
            "extra_txt": "<div>Some more information about the event</div>",
            "replace_all": False,
            "email_type": "event"
        }

        response = client.post(
            url_for('emails.create_email'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))

        assert json_resp['message'] == 'event not found: {}'.format(sample_uuid)
        emails = Email.query.all()
        assert not emails


class WhenPostingUpdateEmail:

    def it_updates_an_event_email(self, mocker, client, db, db_session, sample_email):
        data = {
            "event_id": str(sample_email.event_id),
            "details": sample_email.details,
            "extra_txt": '<div>New extra text</div>',
            "replace_all": sample_email.replace_all,
            "email_type": EVENT
        }

        response = client.post(
            url_for('emails.update_email', email_id=str(sample_email.id)),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['extra_txt'] == data['extra_txt']
        emails = Email.query.all()
        assert len(emails) == 1
        assert emails[0].extra_txt == data['extra_txt']

    def it_errors_when_incorrect_event_id(self, mocker, client, db, db_session, sample_email, sample_uuid):
        data = {
            "event_id": sample_uuid,
            "details": sample_email.details,
            "extra_txt": '<div>New extra text</div>',
            "replace_all": sample_email.replace_all,
            "email_type": EVENT
        }

        response = client.post(
            url_for('emails.update_email', email_id=str(sample_email.id)),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == 'event not found: {}'.format(sample_uuid)

    def it_updates_an_event_email_to_ready(self, mocker, client, db, db_session, sample_admin_user, sample_email):
        mock_send_email = mocker.patch('app.routes.emails.rest.send_smtp_email', return_value=200)
        data = {
            "event_id": str(sample_email.event_id),
            "details": sample_email.details,
            "extra_txt": '<div>New extra text</div>',
            "replace_all": sample_email.replace_all,
            "email_type": EVENT,
            "email_state": READY
        }

        response = client.post(
            url_for('emails.update_email', email_id=str(sample_email.id)),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.json['extra_txt'] == data['extra_txt']
        emails = Email.query.all()
        assert len(emails) == 1
        assert emails[0].extra_txt == data['extra_txt']

        assert mock_send_email.call_args[0][0] == [TEST_ADMIN_USER]

    def it_updates_a_magazine_email_to_ready(
        self, mocker, client, db, db_session, sample_admin_user, sample_magazine_email
    ):
        mock_send_email = mocker.patch('app.routes.emails.rest.send_smtp_email', return_value=200)
        data = {
            "magazine_id": str(sample_magazine_email.magazine_id),
            "details": sample_magazine_email.details,
            "extra_txt": '<div>New extra text</div>',
            "replace_all": sample_magazine_email.replace_all,
            "email_type": MAGAZINE,
            "email_state": READY
        }

        response = client.post(
            url_for('emails.update_email', email_id=str(sample_magazine_email.id)),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.json['extra_txt'] == data['extra_txt']
        emails = Email.query.all()
        assert len(emails) == 1
        assert emails[0].extra_txt == data['extra_txt']

        assert mock_send_email.call_args[0][0] == [TEST_ADMIN_USER]

    def it_updates_an_event_email_to_rejected(
        self, mocker, client, db, db_session, sample_admin_user, sample_email
    ):
        mock_send_email = mocker.patch('app.routes.emails.rest.send_smtp_email', return_value=200)

        data = {
            "event_id": str(sample_email.event_id),
            "details": sample_email.details,
            "extra_txt": '<div>New extra text</div>',
            "replace_all": sample_email.replace_all,
            "email_type": EVENT,
            "email_state": REJECTED,
            "reject_reason": 'test reason'
        }

        response = client.post(
            url_for('emails.update_email', email_id=str(sample_email.id)),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['extra_txt'] == data['extra_txt']
        emails = Email.query.all()
        assert len(emails) == 1
        assert emails[0].extra_txt == data['extra_txt']
        assert emails[0].email_state == REJECTED

        assert mock_send_email.call_args[0][0] == [TEST_ADMIN_USER]
        assert mock_send_email.call_args[0][1] == "test title email needs to be corrected"
        assert mock_send_email.call_args[0][2] == (
            '<div>Please correct this email <a href="http://frontend-test/admin/'
            'emails/{}">workshop: test title</a>'
            '</div><div>Reason: test reason</div>'.format(str(sample_email.id))
        )

    @pytest.mark.parametrize('now,delay', [
        ("2019-07-01 10:00:00", datetime.strptime("2019-08-08", "%Y-%m-%d") + timedelta(hours=9)),
        ("2019-08-09 10:00:00", datetime.strptime("2019-08-09 10", "%Y-%m-%d %H") + timedelta(hours=1))
    ])
    def it_updates_an_event_email_to_approved(
        self, mocker, app, client, db, db_session, sample_admin_user, sample_email, now, delay
    ):
        mock_send_email = mocker.patch('app.routes.emails.rest.send_smtp_email', return_value=200)

        with freeze_time(now):
            data = {
                "event_id": str(sample_email.event_id),
                "details": sample_email.details,
                "extra_txt": '<div>New extra text</div>',
                "replace_all": sample_email.replace_all,
                "email_type": EVENT,
                "email_state": APPROVED,
                "send_starts_at": "2019-08-08",
                "reject_reason": 'test reason'
            }

            response = client.post(
                url_for('emails.update_email', email_id=str(sample_email.id)),
                data=json.dumps(data),
                headers=[('Content-Type', 'application/json'), create_authorization_header()]
            )

            assert response.json['extra_txt'] == data['extra_txt']
            emails = Email.query.all()
            assert len(emails) == 1
            assert emails[0].email_state == data['email_state']
            assert emails[0].extra_txt == data['extra_txt']
            assert emails[0].send_after == delay

            assert mock_send_email.call_args[0][0] == [TEST_ADMIN_USER]
            assert mock_send_email.call_args[0][1] == "{} has been approved".format(emails[0].get_subject())

    def it_raises_error_if_email_not_found(
        self, mocker, client, db_session, sample_email, sample_uuid
    ):
        data = {
            "event_id": str(sample_email.event_id),
            "details": sample_email.details,
            "extra_txt": '<div>New extra text</div>',
            "replace_all": sample_email.replace_all,
            "email_type": EVENT,
            "email_state": READY
        }

        mocker.patch('app.routes.emails.rest.dao_get_email_by_id', side_effect=NoResultFound())

        response = client.post(
            url_for('emails.update_email', email_id=sample_uuid),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))

        assert json_resp['message'] == '{} did not update email'.format(sample_uuid)

    def it_raises_error_if_email_not_updated(
        self, mocker, client, db_session, sample_email
    ):
        data = {
            "event_id": str(sample_email.event_id),
            "details": sample_email.details,
            "extra_txt": '<div>New extra text</div>',
            "replace_all": sample_email.replace_all,
            "email_type": EVENT,
            "email_state": READY
        }

        mocker.patch('app.routes.emails.rest.dao_update_email', return_value=False)

        response = client.post(
            url_for('emails.update_email', email_id=sample_email.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == '{} did not update email'.format(sample_email.id)


class WhenPostingImportingEmailsMailings:
    def it_creates_email_to_members_for_imported_emailmailingss(self, client, db_session, sample_email, sample_member):
        member = create_member(old_id=2, name='Jack Green', email='jack@example.com')
        data = [
            {"id": "1", "emailid": "1", "mailinglistid": "1", "timestamp": "2019-06-10 17:30:00"},
            {"id": "2", "emailid": "1", "mailinglistid": "2", "timestamp": "2019-06-11 17:30:00"},
        ]

        response = client.post(
            url_for('emails.import_emails_members_sent_to'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 201
        assert response.json['emails_members_sent_to'][0]['email_id'] == str(sample_email.id)
        assert response.json['emails_members_sent_to'][0]['member_id'] == str(sample_member.id)
        assert response.json['emails_members_sent_to'][0]['created_at'] == data[0]['timestamp']
        assert response.json['emails_members_sent_to'][1]['email_id'] == str(sample_email.id)
        assert response.json['emails_members_sent_to'][1]['member_id'] == str(member.id)
        assert response.json['emails_members_sent_to'][1]['created_at'] == data[1]['timestamp']

    def it_doesnt_create_email_to_member_if_email_not_found(self, client, db_session, sample_member):
        data = [
            {"id": "1", "emailid": "1", "mailinglistid": "1", "timestamp": "2019-06-10 17:30:00"},
        ]

        response = client.post(
            url_for('emails.import_emails_members_sent_to'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400
        assert response.json['errors'] == ['0: Email not found: 1']

    def it_doesnt_create_email_to_member_if_member_not_found(self, client, db_session, sample_email):
        data = [
            {"id": "1", "emailid": "1", "mailinglistid": "1", "timestamp": "2019-06-10 17:30:00"},
        ]

        response = client.post(
            url_for('emails.import_emails_members_sent_to'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400
        assert response.json['errors'] == ['0: Member not found: 1']

    def it_doesnt_create_email_to_member_if_already_imported(self, client, db_session, sample_email, sample_member):
        dao_add_member_sent_to_email(sample_email.id, sample_member.id)
        data = [
            {"id": "1", "emailid": "1", "mailinglistid": "1", "timestamp": "2019-06-10 17:30:00"},
        ]

        response = client.post(
            url_for('emails.import_emails_members_sent_to'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400
        assert response.json['errors'] == [
            '0: Already exists email_to_member {}, {}'.format(str(sample_email.id), str(sample_member.id))]


class WhenPostingSendMessage:
    def it_sends_message_to_admin_emails(self, client, mocker, db_session, sample_admin_user):
        mock_send_email = mocker.patch('app.routes.emails.rest.send_smtp_email')

        data = {
            "name": "Test email",
            "email": "test@example.com",
            "reason": "Make contact",
            "message": "Test message"
        }

        response = client.post(
            url_for('emails.send_message'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert mock_send_email.called
        assert mock_send_email.call_args == call(
            [sample_admin_user.email], 'Web message: {}'.format(data['reason']), data['message'],
            from_email=data['email'], from_name=data['name']
        )


class WhenGettingDefaultDetails:
    @pytest.mark.parametrize('fee,fee_text', [
        (0, "<div><strong>Fees:</strong> Free Admission</div>"),
        (-2, "<div><strong>Fees:</strong> External site</div>"),
        (-3, "<div><strong>Fees:</strong> Donation</div>"),
        (5, "<div><strong>Fees:</strong> £5, £3 concession for students, "
            "income support & OAPs, and free for members of New Acropolis.</div>")
    ])
    def it_gets_default_details(self, client, sample_event, fee, fee_text):
        sample_event.fee = fee
        response = client.get(
            url_for('emails.get_default_details', event_id=sample_event.id),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.json['details'] == f'{fee_text}<div><strong>Venue:</strong> {sample_event.venue.address}</div>'\
            f'{sample_event.venue.directions}'
