from app.models import Order


def dao_get_orders():
    return Order.query.order_by(Order.created_at).all()


def dao_get_order_with_txn_id(txn_id):
    return Order.query.filter_by(txn_id=txn_id).order_by(Order.created_at).first()
