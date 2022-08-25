import base64
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
    dao_update_book,
    dao_get_book_by_id
)
from app.errors import register_errors, InvalidRequest

from app.routes.books.schemas import post_import_books_schema, post_update_book_schema, post_create_book_schema

from app.models import Book
from app.schema_validation import validate

from app.utils.storage import Storage


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


@book_blueprint.route('/book/<uuid:book_id>', methods=['POST'])
@jwt_required
def update_book(book_id):
    data = request.get_json(force=True)

    validate(data, post_update_book_schema)

    fetched_book = dao_get_book_by_id(book_id)
    if not fetched_book:
        raise InvalidRequest(f'book not found: {book_id}', 404)

    image_data = data.pop('image_data')

    dao_update_book(book_id, **data)

    if image_data:
        target_image_filename = f"books/{fetched_book.title.lower().replace(' ', '-')}.jpg"
        storage = Storage(current_app.config['STORAGE'])

        storage.upload_blob_from_base64string(
            data['image_filename'], target_image_filename, base64.b64decode(image_data))

    return jsonify(fetched_book.serialize()), 201


@book_blueprint.route('/book', methods=['POST'])
@jwt_required
def add_book():
    data = request.get_json(force=True)

    validate(data, post_create_book_schema)

    book = Book(
        title=data['title'],
        author=data['author'],
        image_filename=data['image_filename'],
        description=data['description'],
        price=data['price']
    )

    dao_create_book(book)

    if current_app.config['STORAGE'].startswith('None'):
        current_app.logger.warn('Storage not setup')
    else:
        image_data = data.get('image_data')
        if image_data:
            target_image_filename = f"books/{book.title.lower().replace(' ', '-')}.jpg"
            storage = Storage(current_app.config['STORAGE'])

            storage.upload_blob_from_base64string(
                data['image_filename'], target_image_filename, base64.b64decode(image_data))

    return jsonify(book.serialize()), 201


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
                description=item['LongDesc'],
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
