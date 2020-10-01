import os
from random import randint
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)

from flask_jwt_extended import jwt_required

from app.dao.books_dao import (
    dao_create_book,
    dao_get_books,
    # dao_update_book,
    dao_get_book_by_id
)
from app.errors import register_errors

from app.routes.books.schemas import post_import_books_schema

from app.models import Book
from app.schema_validation import validate

books_blueprint = Blueprint('books', __name__)
book_blueprint = Blueprint('book', __name__)
register_errors(books_blueprint)
register_errors(book_blueprint)


@books_blueprint.route('/books')
@jwt_required
def get_books():
    books = [a.serialize() if a else None for a in dao_get_books()]
    return jsonify(books)


@book_blueprint.route('/book/<uuid:book_id>', methods=['GET'])
@jwt_required
def get_book_by_id(book_id):
    book = dao_get_book_by_id(book_id)
    return jsonify(book.serialize())


@books_blueprint.route('/books/import', methods=['POST'])
@jwt_required
def import_books():
    data = request.get_json(force=True)

    validate(data, post_import_books_schema)

    books = []
    errors = []
    for item in data:
        err = ''
        book = Book.query.filter(Book.old_id == item['id']).first()
        if not book:
            book = Book(
                old_id=item['id'],
                title=item['Title'],
                author=item['Author'],
                image_filename=item['ImageFilename'],
                description=item['Description'],
                long_description=item['LongDesc'],
                price=item['Price'],
                buy_code=item['BuyCode']
            )

            books.append(book)
            dao_create_book(book)
        else:
            err = u'book already exists: {} - {}'.format(book.old_id, book.title)
            current_app.logger.info(err)
            errors.append(err)

    res = {
        "books": [b.serialize() for b in books]
    }

    if errors:
        res['errors'] = errors

    return jsonify(res), 201 if books else 400 if errors else 200
