from freezegun import freeze_time
import pytest

from app.config import get_beat_schedule
from app.na_celery.periodic_tasks import run_periodic_tasks

class MockedObject:
    def __init__(self, name):
        self.__name__ = name
        self.called = False

    def apply_async(self):
        self.called = True


@pytest.fixture
def mock_periodic(mocker):
    mocker.patch(
        'app.na_celery.periodic_tasks.get_config_beat_schedule',
        return_value=get_beat_schedule('test')
    )
    mock_send_periodic_emails_task = mocker.patch(
        'app.na_celery.email_tasks.send_periodic_emails_task',
        MockedObject('send_periodic_emails_task'))
    mock_send_missing_confirmation_emails_task = mocker.patch(
        'app.na_celery.email_tasks.send_missing_confirmation_emails_task',
        MockedObject('send_missing_confirmation_emails_task'))
    mock_send_event_email_reminder_task = mocker.patch(
        'app.na_celery.event_tasks.send_event_email_reminder_task',
        MockedObject('send_event_email_reminder_task'))
    mocker.patch('app.na_celery.periodic_tasks.TASK_LIST', [
        mock_send_periodic_emails_task,
        mock_send_missing_confirmation_emails_task,
        mock_send_event_email_reminder_task
    ])

    return {
        "mock_send_periodic_emails_task" : mock_send_periodic_emails_task,
        "mock_send_missing_confirmation_emails_task": mock_send_missing_confirmation_emails_task,
        "mock_send_event_email_reminder_task": mock_send_event_email_reminder_task
    }


class WhenProcessingPeriodicTasks:

    @freeze_time("2026-09-26T10:00:00")
    def it_calls_periodic_tasks_at_10am(self, mocker, app, mock_periodic):
        run_periodic_tasks()

        assert mock_periodic["mock_send_periodic_emails_task"].called
        assert not mock_periodic["mock_send_missing_confirmation_emails_task"].called
        assert mock_periodic["mock_send_event_email_reminder_task"].called

    @freeze_time("2026-09-26T09:00:00")
    def it_calls_periodic_tasks_at_9am(self, mocker, app, mock_periodic):
        run_periodic_tasks()

        assert mock_periodic["mock_send_periodic_emails_task"].called
        assert mock_periodic["mock_send_missing_confirmation_emails_task"].called
        assert not mock_periodic["mock_send_event_email_reminder_task"].called
