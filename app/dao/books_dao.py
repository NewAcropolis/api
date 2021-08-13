from app import db
from app.dao.decorators import transactional
from app.models import Book, BookToOrder


@transactional
def dao_create_book(book):
    db.session.add(book)


@transactional
def dao_update_book(book_id, **kwargs):
    return Book.query.filter_by(id=book_id).update(
        kwargs
    )


def dao_get_books():
    return Book.query.order_by(Book.title).all()


def dao_get_book_by_id(book_id):
    return Book.query.filter_by(id=book_id).first()


def dao_get_book_by_old_id(old_book_id):
    return Book.query.filter_by(old_id=old_book_id).first()


@transactional
def dao_create_book_to_order(book_to_order):
    db.session.add(book_to_order)


@transactional
def dao_update_book_to_order_quantity(book_id, order_id, quantity):
    t = BookToOrder.query.filter_by(book_id=book_id, order_id=order_id).one()
    t.quantity = quantity
