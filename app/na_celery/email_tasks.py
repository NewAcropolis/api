from datetime import datetime, timedelta
from flask import current_app
import pytz

from app import celery
from app.comms.email import send_email, get_email_html, get_email_provider
from app.comms.stats import send_ga_event
from app.dao.emails_dao import dao_get_email_by_id, dao_add_member_sent_to_email, dao_get_approved_emails_for_sending
from app.dao.members_dao import dao_get_members_not_sent_to
from app.dao.users_dao import dao_get_admin_users
from app.errors import InvalidRequest
from app.models import EVENT, MAGAZINE, APPROVED


def send_emails(email_id):
    members_not_sent_to = dao_get_members_not_sent_to(email_id)

    if current_app.config.get('EMAIL_RESTRICT'):
        limit = 1
    elif current_app.config.get('ENVIRONMENT') == 'live':
        email_provider = get_email_provider()
        limit = email_provider.limit
    else:
        limit = current_app.config.get('EMAIL_LIMIT')

    current_app.logger.info(
        'Task send_emails received %s, sending %d emails',
        str(email_id),
        len(members_not_sent_to) if len(members_not_sent_to) < limit else limit
    )

    email = dao_get_email_by_id(email_id)

    try:
        for index, (member_id, email_to) in enumerate(members_not_sent_to):
            if limit and index > limit - 1 or email.email_state != APPROVED:
                current_app.logger.info("Email stopped - {}".format(
                    "not approved" if email.email_state != APPROVED else "limit reached"))
                break
            subject = email.get_subject()
            message = None
            if email.email_type == EVENT:
                message = get_email_html(
                    email.email_type,
                    event_id=email.event_id,
                    details=email.details,
                    extra_txt=email.extra_txt,
                    member_id=member_id
                )
            elif email.email_type == MAGAZINE:
                message = get_email_html(MAGAZINE, magazine_id=email.magazine_id, member_id=member_id)

            email_status_code, email_provider_id = send_email(email_to, subject, message)
            dao_add_member_sent_to_email(
                email_id, member_id, status_code=email_status_code,
                email_provider_id=email_provider_id
            )

            send_ga_event(
                f"Sent {email.email_type} email, {subject} - {str(email.id)}",
                "email",
                "send success" if email_status_code in [200, 201] else "send failed",
                f"{subject} - {email.id}")
    except InvalidRequest as e:
        if e.status_code == 429:
            current_app.logger.error("Email limit reached: %r", e.message)
        else:
            raise


@celery.task(name='send_periodic_emails')
def send_periodic_emails():
    tz_London = pytz.timezone('Europe/London')
    current_time = datetime.strftime(datetime.now(tz_London), "%H:%M:%S")

    if current_app.config.get('EMAIL_ANYTIME'):
        current_app.logger.info('Email anytime config set')
    else:
        if current_app.config['ENVIRONMENT'] != 'development' and \
                (current_time < current_app.config['EMAIL_EARLIEST_TIME'] or
                    current_time > current_app.config['EMAIL_LATEST_TIME']):
            current_app.logger.info('Task send_periodic_emails received: not between 8am and 10pm')
            return

    emails = dao_get_approved_emails_for_sending()
    current_app.logger.info('Task send_periodic_emails received: {}'.format(
        ", ".join([str(e.id) for e in emails]) if emails else 'no emails to send'))

    for email in emails:
        send_emails(email.id)
