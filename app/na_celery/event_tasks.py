from datetime import datetime, timedelta
from flask import current_app
import pytz

from app import celery
from app.comms.email import send_admin_email, get_email_html, get_email_provider
from app.dao.emails_dao import dao_get_email_by_event_id
from app.dao.events_dao import dao_get_future_events
from app.dao.users_dao import dao_get_admin_users
from app.models import BASIC


@celery.task(name='send_event_email_reminder')
def send_event_email_reminder():
    current_app.logger.info('Task send_event_email_reminder received: {}')

    for event in dao_get_future_events():
        event.event_dates.sort(key=lambda k: k.event_datetime)

        time_to_send = (event.event_dates[0].event_datetime - timedelta(weeks=2)) < datetime.today()

        if time_to_send and not dao_get_email_by_event_id(event.id):
            subject = f"Event: {event.title} email reminder"
            message = f"Please <a href='{current_app.config['FRONTEND_ADMIN_URL']}/emails'>"\
                f"login</a> to createa an email for {event.title}"
            message_html = get_email_html(BASIC, message=message)

            for user in dao_get_admin_users():
                status_code = send_admin_email(user.email, subject, message_html)
                if status_code != 200:
                    current_app.logger.error(
                        f"Problem sending reminder email {subject} for {user.id}, status code: {status_code}")
