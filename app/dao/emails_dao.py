from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from sqlalchemy.orm.exc import NoResultFound

from app import db
from app.dao.decorators import transactional
from app.dao.events_dao import dao_get_event_by_id
from app.dao.members_dao import dao_get_member_by_id
from app.errors import InvalidRequest
from app.models import Email, EmailToMember, EVENT, APPROVED


@transactional
def dao_create_email(email):
    if email.email_type == EVENT:
        try:
            event = dao_get_event_by_id(email.event_id)
            if not email.send_starts_at:
                email.send_starts_at = datetime.strptime(event.get_first_event_date(), "%Y-%m-%d") - timedelta(weeks=2)
            if not email.expires:
                email.expires = event.get_last_event_date()
        except NoResultFound:
            raise InvalidRequest('event not found: {}'.format(email.event_id), 400)

    db.session.add(email)


@transactional
def dao_update_email(email_id, **kwargs):
    if 'members_sent_to' in kwargs.keys():
        members_sent_to = kwargs.pop('members_sent_to')
    else:
        members_sent_to = None

    email_query = Email.query.filter_by(id=email_id)

    res = email_query.update(kwargs) if kwargs else None

    if members_sent_to is not None:
        email_query.one().members_sent_to = members_sent_to

    return res


@transactional
def dao_add_member_sent_to_email(email_id, member_id, status_code=200, created_at=None):
    if not created_at:
        created_at = datetime.strftime(datetime.now(), "%Y-%m-%d")

    email = dao_get_email_by_id(email_id)
    member = dao_get_member_by_id(member_id)

    if email.members_sent_to:
        email.members_sent_to.append(member)
    else:
        email.members_sent_to = [member]

    email_to_member = EmailToMember.query.filter_by(email_id=email.id, member_id=member.id).first()
    email_to_member.created_at = created_at
    email_to_member.status_code = status_code


@transactional
def dao_create_email_to_member(email_to_member):
    db.session.add(email_to_member)


def dao_get_emails_for_year_starting_on(date_starting=None):
    if not date_starting:
        date_starting = (datetime.today() - timedelta(weeks=52)).strftime("%Y-%m-%d")
        date_ending = datetime.today().strftime("%Y-%m-%d")
    else:
        date_ending = (datetime.strptime(date_starting, "%Y-%m-%d") + timedelta(weeks=52)).strftime("%Y-%m-%d")

    return Email.query.filter(
        and_(
            Email.created_at >= date_starting,
            Email.created_at < date_ending
        )
    ).order_by(Email.created_at.desc()).all()


def dao_get_email_by_id(email_id):
    return Email.query.filter_by(id=email_id).one()


def dao_get_future_emails():
    today = datetime.today().strftime("%Y-%m-%d")
    return Email.query.filter(
        Email.expires >= today
    ).all()


def dao_get_approved_emails_for_sending():
    now = datetime.today()
    emails = Email.query.all()

    return Email.query.filter(
        Email.expires >= now,
        Email.send_after <= now,
        Email.email_state == APPROVED
    ).all()
