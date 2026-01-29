from uuid import UUID

from datetime import datetime, timedelta
from pytz import timezone
from sqlalchemy import and_

from app import db
from app.dao.decorators import transactional
from app.models import Email, EmailToMember, Member


@transactional
def dao_create_member(member):
    db.session.add(member)


@transactional
def dao_update_member(member_id, **kwargs):
    now = datetime.now(timezone('Europe/London'))
    kwargs['last_updated'] = now
    return Member.query.filter_by(id=member_id).update(
        kwargs
    )


def dao_get_members():
    return Member.query.all()


def dao_get_first_member():
    return Member.query.first()


def _get_end_month_year(month, year, end_month=None, end_year=None):
    if end_month and end_year:
        end_month = int(end_month) + 1
    else:
        end_month = int(month) + 1
        end_year = int(year)
    if end_month > 12:
        end_month = 1
        end_year += 1

    return end_month, end_year


def dao_get_active_member_count(end_month=None, end_year=None):
    if not end_month:
        return Member.query.filter_by(active=True).count()
    else:
        end_month += 1
        if end_month > 12:
            end_month = 1
            end_year += 1
        START_MONTH = 1
        START_YEAR = 2000

        return Member.query.filter(
            and_(
                Member.created_at.between(f'{START_YEAR}-{START_MONTH}-01', f'{end_year}-{end_month}-01'),
                Member.active
            )
        ).count()


def dao_get_new_member_count(month, year, end_month=None, end_year=None):
    end_month, end_year = _get_end_month_year(month, year, end_month, end_year)

    return Member.query.filter(
        and_(
            Member.created_at.between(f'{year}-{month}-01', f'{end_year}-{end_month}-01'),
            Member.active == True  # noqa E711 SqlAlchemy syntax
        )
    ).count()


def dao_get_unsubscribed_member_count(month, year, end_month=None, end_year=None):
    end_month, end_year = _get_end_month_year(month, year, end_month, end_year)

    return Member.query.filter(
        and_(
            Member.last_updated.between(f'{year}-{month}-01', f'{end_year}-{end_month}-01'),
            Member.active == False  # noqa E711 SqlAlchemy syntax
        )
    ).count()


def dao_get_member_by_email(email):
    return Member.query.filter(Member.email.ilike(f"%{email}%")).first()


def dao_get_member_by_id(member_id):
    try:
        UUID(str(member_id), version=4)
        return Member.query.filter_by(id=member_id).one()
    except ValueError as e:
        return Member.query.filter_by(old_id=member_id).one()


def dao_get_members_not_sent_to(email_id, is_reminder=False):
    subquery = db.session.query(EmailToMember.member_id).filter(
        EmailToMember.email_id == email_id, EmailToMember.is_reminder == is_reminder)

    return db.session.query(Member.id, Member.email).filter(
        and_(
            Member.id.notin_(subquery),
            Member.active
        )
    ).all()
