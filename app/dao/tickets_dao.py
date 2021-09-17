from uuid import UUID

from app.dao.decorators import transactional
from app.models import Ticket


def dao_get_tickets_for_order(order_id):
    return Ticket.query.filter_by(order_id=order_id).order_by(Ticket.created_at).all()


def dao_get_tickets_for_event_date(eventdate_id):
    return Ticket.query.filter_by(eventdate_id=eventdate_id).order_by(Ticket.created_at).all()


@transactional
def dao_update_ticket(ticket_id, **kwargs):
    try:
        UUID(ticket_id, version=4)
        return Ticket.query.filter_by(id=ticket_id).update(
            kwargs
        )
    except ValueError:
        return Ticket.query.filter_by(old_id=ticket_id).update(
            kwargs
        )


def dao_get_ticket_id(ticket_id):
    try:
        UUID(ticket_id, version=4)
        return Ticket.query.filter_by(id=ticket_id).first()
    except ValueError:
        return Ticket.query.filter_by(old_id=ticket_id).first()
