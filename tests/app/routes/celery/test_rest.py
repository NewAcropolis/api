import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask import url_for
from tests.conftest import create_authorization_header


class WhenGettingCelery(object):

    def it_calls_celery_send_periodic_emails(self, client, mocker):
        mock_call_send_periodic_emails_task = mocker.patch(
            "app.na_celery.email_tasks.send_periodic_emails_task.apply_async", return_value=None)
        response = client.get(
            url_for('celery.celery_send_periodic_emails'),
            headers=[create_authorization_header()]
        )
        assert mock_call_send_periodic_emails_task.called
        assert response.status_code == 200

        data = response.get_data(as_text=True)

        assert data == "ok"

    def it_calls_celery_send_event_email_reminder(self, client, mocker):
        mock_call_send_event_reminder_email = mocker.patch(
            "app.na_celery.event_tasks.send_event_email_reminder_task.apply_async", return_value=None)
        response = client.get(
            url_for('celery.celery_send_event_email_reminder'),
            headers=[create_authorization_header()]
        )
        assert mock_call_send_event_reminder_email.called
        assert response.status_code == 200

        data = response.get_data(as_text=True)

        assert data == "ok"
