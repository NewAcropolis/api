from datetime import datetime, timedelta
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask import current_app
import pytz

from app import celery
from app.comms.email import send_email, get_email_html, get_email_provider
from app.comms.stats import send_ga_event
from app.dao import dao_update_record
from app.dao.emails_dao import (
    dao_get_email_by_id, dao_add_member_sent_to_email, dao_get_approved_emails_for_sending, dao_has_child_email
)
from app.dao.members_dao import dao_get_members_not_sent_to, dao_get_first_member
from app.dao.orders_dao import dao_get_orders_without_email_status
from app.dao.users_dao import dao_get_admin_users
from app.errors import InvalidRequest
from app.models import BASIC, EVENT, MAGAZINE, APPROVED, Order
from app.routes.orders.rest import _replay_paypal_ipn


def send_emails(email_id):
    if current_app.config.get('EMAIL_TEST'):
        member = dao_get_first_member()
        members_not_sent_to = [(member.id, member.email)]
    else:
        members_not_sent_to = dao_get_members_not_sent_to(email_id)

    if current_app.config.get('EMAIL_RESTRICT') or current_app.config.get('EMAIL_TEST'):
        limit = 1
    elif current_app.config.get('ENVIRONMENT') == 'live':
        email_provider = get_email_provider(use_minute_limit=False)
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
                    "not approved" if email.email_state != APPROVED else f"limit reached: {limit}"))
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
            elif email.email_type == BASIC:
                message = get_email_html(BASIC, message=email.extra_txt)

            email_status_code, email_provider_id = send_email(email_to, subject, message)
            if not current_app.config.get('EMAIL_TEST'):
                dao_add_member_sent_to_email(
                    email_id, member_id, status_code=email_status_code,
                    email_provider_id=email_provider_id
                )

            send_ga_event(
                f"Sent {email.email_type} email, {subject} - {str(email.id)}",
                "email",
                "send success" if email_status_code in [200, 201, 202] else "send failed",
                f"{subject} - {email.id}")
    except InvalidRequest as e:
        if e.status_code == 429:
            current_app.logger.error("Email limit reached: %r", e.message)
            if "Minute" in e.message:
                send_periodic_emails.apply_async(countdown=60)
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
        if not dao_has_child_email(email.id):
            send_emails(email.id)


@celery.task(name='send_missing_confirmation_emails')
def send_missing_confirmation_emails():
    for order in dao_get_orders_without_email_status():
        email_status_code = _replay_paypal_ipn(order.txn_id, email_only=True)
        if not email_status_code:
            dao_update_record(
                Order, order.id,
                email_status='500'
            )
