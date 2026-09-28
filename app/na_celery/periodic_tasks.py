from datetime import datetime
from flask import  Flask
import os

from app.config import configs
from app.na_celery.email_tasks import send_periodic_emails_task, send_missing_confirmation_emails_task
from app.na_celery.event_tasks import send_event_email_reminder_task

TASK_LIST = [send_periodic_emails_task, send_missing_confirmation_emails_task, send_event_email_reminder_task]


def should_run_now(schedule):
    _datetime = datetime.now()
    return _datetime.day in schedule.day_of_month and _datetime.hour in schedule.hour


def get_config_beat_schedule(app): # pragma: no cover
    app.config.from_object(configs[os.environ.get('ENVIRONMENT', 'development')])
    return app.config.get("BEAT_SCHEDULE")


def run_periodic_tasks():
    app = Flask(__name__)
    beat_schedule = get_config_beat_schedule(app)
    for beat in beat_schedule:
        for task in TASK_LIST:
            if beat_schedule[beat]['task'] == task.__name__[:-5]:  # trim _task from end of method name
                if should_run_now(beat_schedule[beat]['schedule']):
                    task.apply_async()
                    print(task.__name__)

    print(app.config.get("BEAT_SCHEDULE"))
