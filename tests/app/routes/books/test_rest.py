from flask import json, url_for
from tests.conftest import create_authorization_header


sample_books_for_import = [{
    "id": "1",
    "FormatId": "1",
    "Title": "The Alchemist",
    "ShortTitle": "Alchemist",
    "Description": "is a historical novel about an aspiring young chemist who is a member of a Hermetic Lodge in the "
                   "16th Century. ",
    "LongDesc": "<p>Set in the times of the Spanish Inquisition, this historical novel describes the secret life of an "
                "esoteric lodge in the darkest times of the “Counter-Reformation”.</p>\r\n<p>Amidst the constant "
                "dangers of discovery and potential torture and execution, Pablo Simón, a young aspirant to the "
                "Mysteries, learns about the universe as a living being\r\nand begins to discover another universe "
                "within himself.</p>",
    "Author": "Jorge A Livraga",
    "ImageFilename": "BookAlchemist.png",
    "WebLink": "",
    "Price": "7.00",
    "BuyCode": "XXYXXYXXYYXYY",
    "Active": "y"
}, {
    "id": "2",
    "FormatId": "1",
    "Title": "Thebes",
    "ShortTitle": "Thebes",
    "Description": "is a full colour, 163 page book on Ancient Egypt that gives the reader an in-depth understanding "
                   "of the ancient Egyptian vision. This includes, amongst other topics, information about the "
                   "Pyramids, the hieroglyphs and the hidden purpose of mummification.",
    "LongDesc": "Thebes is a full colour, 163 page book on an in-depth understanding of the ancient Egyptian vision. "
                "This includes, amongst other topics, information about the Pyramids, the hieroglyphs and the hidden "
                "purpose of mummification.<br><br>\r\nIt offers a unique comparison between the officially accepted "
                "history of Egypt and alternative versions, including the connection between Atlantis and Egypt.",
    "Author": "Jorge A Livraga",
    "ImageFilename": "BookThebes.png",
    "WebLink": "",
    "Price": "7.00",
    "BuyCode": "XXXYYYXXXYYXX",
    "Active": "y"
}]


class WhenPostingImportBooks(object):

    def it_creates_books_for_imported_books(self, client, db_session):
        response = client.post(
            url_for('books.import_books'),
            data=json.dumps(sample_books_for_import),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_books = json.loads(response.get_data(as_text=True))['books']
        assert len(json_books) == len(sample_books_for_import)
        for i in range(0, len(sample_books_for_import) - 1):
            assert json_books[i]["old_id"] == int(sample_books_for_import[i]["id"])
            assert json_books[i]["title"] == sample_books_for_import[i]["Title"]
            assert json_books[i]["author"] == sample_books_for_import[i]["Author"]

    def it_does_not_create_book_for_imported_books_with_duplicates(self, client, db_session):
        duplicate_book = {
            "id": "1",
            "FormatId": "1",
            "Title": "The Alchemist",
            "Author": "Jorge A Livraga",
            "ImageFilename": "BookAlchemist.png",
            "WebLink": "",
            "Price": "7.00",
            "BuyCode": "XXYXXYXXYYXYY",
            "Active": "y"
        },

        sample_books_for_import.extend(duplicate_book)

        response = client.post(
            url_for('books.import_books'),
            data=json.dumps(sample_books_for_import),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_books = json.loads(response.get_data(as_text=True))['books']
        assert len(json_books) == len(sample_books_for_import) - 1  # don't add in duplicate book
        for i in range(0, len(sample_books_for_import) - 1):
            assert json_books[i]["old_id"] == int(sample_books_for_import[i]["id"])
            assert json_books[i]["title"] == sample_books_for_import[i]["Title"]
            assert json_books[i]["author"] == sample_books_for_import[i]["Author"]


class WhenPostingUpdateBook:

    def it_updates_a_book(self, client, db_session, sample_book):
        data = {
            'buy_code': 'NEW_BUY_CODE',
            'price': '5.00'
        }

        response = client.post(
            url_for('book.update_book', book_id=sample_book.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201
        assert response.json['buy_code'] == data['buy_code']
        assert response.json['price'] == data['price']

    def it_returns_invalid_request(self, client, db_session, sample_uuid):
        data = {
            'buy_code': 'NEW_BUY_CODE',
            'price': '5.00'
        }

        response = client.post(
            url_for('book.update_book', book_id=sample_uuid),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 404


class WhenGettingBooks:

    def it_returns_all_books(self, client, db_session, sample_book):
        response = client.get(
            url_for('books.get_books'),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        assert len(response.json) == 1
        assert response.json[0]['id'] == str(sample_book.id)


class WhenGettingBookByID:

    def it_returns_correct_book(self, client, sample_book, db_session):
        response = client.get(
            url_for('book.get_book_by_id', book_id=str(sample_book.id)),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        assert response.json['id'] == str(sample_book.id)
