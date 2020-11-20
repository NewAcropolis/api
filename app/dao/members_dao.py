from uuid import UUID

from datetime import datetime, timedelta
from sqlalchemy import and_

from app import db
from app.dao.decorators import transactional
from app.models import Email, EmailToMember, Member


@transactional
def dao_create_member(member):
    db.session.add(member)


@transactional
def dao_update_member(member_id, **kwargs):
    return Member.query.filter_by(id=member_id).update(
        kwargs
    )


def dao_get_members():
    return Member.query.all()


def dao_get_active_member_count():
    return Member.query.filter_by(active=True).count()


def dao_get_member_by_email(email):
    return Member.query.filter_by(email=email).first()


def dao_get_member_by_id(member_id):
    try:
        UUID(str(member_id), version=4)
        return Member.query.filter_by(id=member_id).one()
    except ValueError as e:
        return Member.query.filter_by(old_id=member_id).one()


def dao_get_members_not_sent_to(email_id):
    subquery = db.session.query(EmailToMember.member_id).filter(EmailToMember.email_id == email_id)

    return db.session.query(Member.id, Member.email).filter(
        and_(
            Member.id.notin_(subquery),
            Member.active
        )
    ).all()
