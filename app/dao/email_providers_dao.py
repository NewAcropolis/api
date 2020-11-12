import json

from app import db
from app.dao.decorators import transactional
from app.dao.emails_dao import dao_get_past_hour_email_count_for_provider, dao_get_todays_email_count_for_provider
from app.models import EmailProvider


@transactional
def dao_create_email_provider(email_provider):
    if email_provider.data_map:
        email_provider.data_map = json.loads(email_provider.data_map)

    db.session.add(email_provider)


@transactional
def dao_update_email_provider(email_provider_id, **kwargs):
    email_provider_query = EmailProvider.query.filter_by(id=email_provider_id)
    if kwargs.get("data_map"):
        kwargs["data_map"] = json.loads(kwargs["data_map"])

    return email_provider_query.update(kwargs)


def dao_get_first_email_provider():
    return EmailProvider.query.order_by(EmailProvider.pos).first()


def dao_get_email_providers():
    return EmailProvider.query.order_by(EmailProvider.pos).all()


def dao_get_next_email_provider(pos):
    return EmailProvider.query.filter(EmailProvider.pos > pos).order_by(EmailProvider.pos).first()


def dao_get_next_available_email_provider(pos):
    return EmailProvider.query.filter(
        EmailProvider.available,
        EmailProvider.pos > pos
    ).order_by(EmailProvider.pos).first()


def dao_get_email_provider_by_id(email_provider_id):
    return EmailProvider.query.filter_by(id=email_provider_id).one()
