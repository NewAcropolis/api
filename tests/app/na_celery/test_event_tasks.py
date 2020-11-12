from freezegun import freeze_time

from app.na_celery.event_tasks import send_event_email_reminder


class WhenProcessingSendEventEmailReminderTask:

    @freeze_time("2017-12-20T10:00:00")
    def it_sends_the_event_email_reminder(self, mocker, db_session, sample_event_with_dates, sample_admin_user):
        mock_send_email = mocker.patch('app.na_celery.event_tasks.send_smtp_email', return_value=200)

        send_event_email_reminder()

        assert mock_send_email.call_args[0][0] == sample_admin_user.email
        assert mock_send_email.call_args[0][1] == f"Event: {sample_event_with_dates.title} email reminder"

    @freeze_time("2017-12-01T10:00:00")
    def it_does_not_send_the_event_email_reminder_too_early(
        self, mocker, db_session, sample_event_with_dates, sample_admin_user
    ):
        mock_send_email = mocker.patch('app.na_celery.event_tasks.send_smtp_email', return_value=200)

        send_event_email_reminder()

        assert not mock_send_email.called

    @freeze_time("2017-12-20T10:00:00")
    def it_reports_an_error_if_sending_reminder_fails(
        self, mocker, db_session, sample_event_with_dates, sample_admin_user
    ):
        mock_send_email = mocker.patch('app.na_celery.event_tasks.send_smtp_email', return_value=503)
        mock_logger = mocker.patch('app.na_celery.event_tasks.current_app.logger.error')

        send_event_email_reminder()

        assert mock_send_email.call_args[0][0] == sample_admin_user.email
        assert mock_send_email.call_args[0][1] == f"Event: {sample_event_with_dates.title} email reminder"
        assert mock_logger.called
        assert mock_logger.call_args[0][0] == f"Problem sending reminder email Event"\
            f": {sample_event_with_dates.title} email reminder for {sample_admin_user.id}, status code: 503"
