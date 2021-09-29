from datetime import datetime

from app import db
from app.dao.decorators import transactional
from app.models import Order


def dao_get_orders(year=None):
    if not year:
        return Order.query.order_by(Order.created_at).all()
    else:
        start_year = f"{year}-01-01"
        end_year = f"{year + 1}-01-01"
        return Order.query.filter(
            Order.created_at.between(start_year, end_year)
        ).order_by(Order.created_at).all()


def dao_get_order_with_txn_id(txn_id):
    return Order.query.filter_by(txn_id=txn_id).order_by(Order.created_at).first()


@transactional
def dao_delete_order(txn_id):
    order = Order.query.filter_by(txn_id=txn_id).first()
    db.session.delete(order)
