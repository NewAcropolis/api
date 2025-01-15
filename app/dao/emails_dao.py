from datetime import datetime, timedelta
from dateutils import relativedelta
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask import current_app
from pytz import timezone
from sqlalchemy import and_, or_
from sqlalchemy.orm.exc import NoResultFound

from app import db
from app.dao.decorators import transactional
from app.dao.events_dao import dao_get_event_by_id
from app.dao.magazines_dao import dao_get_magazine_by_id
from app.dao.members_dao import dao_get_member_by_id
from app.errors import InvalidRequest
from app.models import Email, EmailToMember, APPROVED, ANNOUNCEMENT, EVENT, MAGAZINE


def _get_nearest_bi_monthly_send_date(created_at=None):
    if not created_at:
        created_at = datetime.today()
    month_offset = 1 if created_at.month % 2 == 0 else 0
    return datetime.strptime('{}-{}-{}'.format(created_at.year, created_at.month, 1), "%Y-%m-%d") +\
        relativedelta(months=month_offset)


@transactional
def dao_create_email(email):
    if email.email_type == EVENT:
        try:
            event = dao_get_event_by_id(email.event_id)
            if dao_get_email_by_event_id(email.event_id):
                raise InvalidRequest('event email already exists: {}'.format(email.event_id), 400)

            email.subject = u"{}: {}".format(event.event_type.event_type, event.title)
            if not email.send_starts_at:
                email.send_starts_at = datetime.strptime(event.get_first_event_date(), "%Y-%m-%d") - timedelta(weeks=2)
            if not email.expires:
                email.expires = event.get_last_event_date()
        except NoResultFound:
            raise InvalidRequest('event not found: {}'.format(email.event_id), 400)
    elif email.email_type == MAGAZINE and not email.old_id:
        if email.magazine_id:
            try:
                magazine = dao_get_magazine_by_id(email.magazine_id)
                if dao_get_email_by_magazine_id(email.magazine_id):
                    raise InvalidRequest('magazine email already exists: {}'.format(email.magazine_id), 400)

                email.subject = u"New Acropolis bi-monthly magazine: {}".format(magazine.title)
                if not email.send_starts_at:
                    email.send_starts_at = _get_nearest_bi_monthly_send_date()
                    email.expires = email.send_starts_at + timedelta(weeks=2)
            except NoResultFound:
                raise InvalidRequest('magazine not found: {}'.format(email.event_id), 400)
        else:
            current_app.logger.info('No magazine id for email')
            return

    db.session.add(email)
    return True


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
def dao_add_member_sent_to_email(email_id, member_id, status_code=200, email_provider_id=None, created_at=None):
    if not created_at:
        created_at = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")

    email = dao_get_email_by_id(email_id)
    member = dao_get_member_by_id(member_id)

    if email.members_sent_to:
        email.members_sent_to.append(member)
    else:
        email.members_sent_to = [member]

    email_to_member = EmailToMember.query.filter_by(email_id=email.id, member_id=member.id).first()
    email_to_member.created_at = created_at
    email_to_member.status_code = status_code
    email_to_member.email_provider_id = email_provider_id


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


def dao_get_email_by_event_id(event_id):
    return Email.query.filter_by(event_id=event_id).first()


def dao_get_email_by_magazine_id(magazine_id):
    return Email.query.filter_by(magazine_id=magazine_id).first()


def dao_get_future_emails():
    today = datetime.today().strftime("%Y-%m-%d")
    return Email.query.filter(
        Email.expires >= today
    ).all()


def dao_get_latest_emails():
    emails = Email.query.order_by(Email.created_at.desc()).limit(30).all()

    latest_emails = []
    magazine_found = False
    for e in emails:
        if e.email_type not in [ANNOUNCEMENT, EVENT, MAGAZINE]:
            continue
        if not e.email_type == MAGAZINE or not magazine_found:
            latest_emails.append(e)
        if e.email_type == MAGAZINE:
            magazine_found = True

    return latest_emails


def dao_get_approved_emails_for_sending():
    now = datetime.now(timezone('Europe/London'))

    return Email.query.filter(
        Email.expires >= now,
        Email.send_after <= now,
        Email.email_state == APPROVED
    ).order_by(Email.expires).all()


def dao_get_last_30_days_email_count_for_provider(email_provider_id):
    now = datetime.now(timezone('Europe/London'))
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return EmailToMember.query.filter(
        EmailToMember.created_at > today,
        EmailToMember.created_at > now - timedelta(days=30),
        EmailToMember.email_provider_id == email_provider_id
    ).count()


def dao_get_todays_email_count_for_provider(email_provider_id):
    now = datetime.now(timezone('Europe/London'))
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    return EmailToMember.query.filter(
        EmailToMember.created_at > today,
        EmailToMember.created_at < today + timedelta(days=1),
        EmailToMember.email_provider_id == email_provider_id
    ).count()


def dao_get_past_hour_email_count_for_provider(email_provider_id):
    now = datetime.now(timezone('Europe/London'))
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    return EmailToMember.query.filter(
        EmailToMember.created_at > now - timedelta(hours=1),
        EmailToMember.email_provider_id == email_provider_id
    ).count()


def dao_get_last_minute_email_count_for_provider(email_provider_id):
    now = datetime.now(timezone('Europe/London'))

    return EmailToMember.query.filter(
        EmailToMember.created_at > now - timedelta(minutes=1),
        EmailToMember.email_provider_id == email_provider_id
    ).count()


def dao_get_emails_sent_count(month=None, year=None):
    if not month:
        month = int(datetime.today().strftime("%m"))
    if not year:
        year = int(datetime.today().strftime("%Y"))

    end_month = month + 1
    end_year = year

    if end_month > 12:
        end_month = 1
        end_year += 1

    return EmailToMember.query.filter(
        EmailToMember.created_at > f"{year}-{month}-01",
        EmailToMember.created_at < f"{end_year}-{end_month}-01"
    ).count()
