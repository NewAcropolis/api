from app import db
from app.dao.decorators import transactional
from app.models import Book


@transactional
def dao_create_book(book):
    db.session.add(book)


# @transactional
# def dao_update_book(book_id, **kwargs):
#     return Book.query.filter_by(id=book_id).update(
#         kwargs
#     )


def dao_get_books():
    return Book.query.order_by(Book.title).all()


def dao_get_book_by_id(book_id):
    return Book.query.filter_by(id=book_id).one()
