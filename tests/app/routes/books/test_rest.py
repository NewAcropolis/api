import base64
import pytest

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

base64img = (
    'iVBORw0KGgoAAAANSUhEUgAAADgAAAAsCAYAAAAwwXuTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAEMElEQVRoge2ZTUxcVRTH'
    '/+fed9+bDxFEQUCmDLWbtibWDE2MCYGa6rabykITA7pV6aruNGlcGFe6c2ui7k1cmZp0YGdR2pjqoklBpkCVykem8/'
    'HeffceF8MgIC3YvDczNP0ls5l3cuf8cuee++65wGMe09LQQQP5xkkXJ4rpjYU40zkY7UcA/NZWopM3gv1iHyg4M5NTuRPrPf5'
    '6cJ4ETgsHg1ZHludDIxQQBphLpOiasfTrtVvPXB4a+nnPzO4rWFnOjroJO25CfkF5UAgBrTm+rP8nyiHAAzgALNNsCHzjdXZdI'
    'dop+h/BmzePeYPd+lXW9pIj4eqAwa3jtSeuV9PQhvKqKC7S4Hy1/myHIHNfSq84nyqXR7Tf+mK7cdMEU6G89O2HlLldAQCxPSD'
    '4U55TaRoJqodPDgCCEkOmaMR38HH9uy3B4tLAceViUt8zzckuInTJwE3QmerikbPApuDaXLbDk3yBCMnDOHPbYQYISEiJC7x6t'
    'F0AQNrzn1dpejnwD7ndJoHPcBKc0WX/uACAkOUr7Ntm5xUp2mdYQR8RAPBa5vqjMnvbceTmGoxajqj2aTah2bVNRAIB1pBmrm3'
    'AzfaMXNBNEqQU3wp2Jo2lWVKbok0yjWUGjWGjeuevyM6Fd2HxgbW4Kh1qiqgT07gEAEQwwO08M6bDu9lhhnnbcWiIBNCod9y4B'
    'HdABAvM55kxFa5khtmIcaVsDhS/aEME6xCBgcIUgCm9lBlmBxNKUQ4UfSWvE/0aPCCqrzDtdhfeCUO8pzX94qp/jz1R0jTBOqq'
    '7MO12L0xUfXq/WsWsktEWoqYL1kn2FaaSvYXxUlVOWkNhVJINXYMPggGqLg+MSrJvMlhGVXhaQlCvDJzRlicSyr5YKzjRjd00Q'
    'WbI8E7/MEkxIaU9BQkEQfSVtOGCvJDps2l6w6ziNSFtRiiObYsAGihYWhnoVYbHNPF5pfhJ6zMMA2HMx7S4BLeyvvdXtsexdgz'
    'WjqkU2sIKIyjH9Kt7EL0gA5aRKC4f61LQ47DmnJdCm26wWB0CAP9O//UoR+TaPqbdJJLN7q/GMoNCsgPACar7RseOAGq9iyhhR'
    'ss0jgUAaI3FVuihRI3rUU1QWL6kYniTbyauR/Cr+FIAgEp5v4dVKsRxXGkGShECjT88Nl8JAKDOWxvG4HNmVB6FvyolBIyhr6l'
    'vqbx1XEo8t3BZB/hCPRFxxWkwtSs0zid7wu+BXedB91nznSlx3k0fzml00wTjU75QFBeJlsrAHje8PJdN6Db7mZI8AsTXK4kSI'
    'QBH0f43vHWYc8pfXRl1gLcE8UukAF1uPVGVItgKw0oqGiM/8bqe/nHfO/rtzMzk1Kmjd8+SNKd1hV4nQKIVPAlgwKgk/6DL8qp'
    'nwp+of/Hv+4QejLW5bEeHsLQRXZoPTTuAdSv4qcH59f1i/wGycsTRKGME7gAAAABJRU5ErkJggg=='
)


def base64img_encoded():
    base64img_encoded = base64.b64encode(base64img.encode())
    base64img_encoded = base64.b64encode(base64img_encoded).decode('utf-8')
    return base64img_encoded


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

    @pytest.fixture
    def mock_storage(self, mocker):
        mock_storage = mocker.patch("app.utils.storage.Storage.__init__", return_value=None)
        mock_storage_blob_exists = mocker.patch("app.utils.storage.Storage.blob_exists")
        mock_upload_blob = mocker.patch("app.utils.storage.Storage.upload_blob_from_base64string")
        yield
        mock_storage.assert_called_with('test-store')
        mock_upload_blob.assert_called_with(
            'test_filename.jpg', 'books/the-spirits-of-nature.jpg', base64.b64encode(base64img.encode()))

    def it_updates_a_book(self, client, db_session, sample_book, mock_storage):
        data = {
            'buy_code': 'NEW_BUY_CODE',
            'price': '5.00',
            'image_filename': 'test_filename.jpg',
            'image_data': base64img_encoded()
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


class WhenPostingCreateBook:

    @pytest.fixture
    def mock_storage(self, mocker):
        mock_storage = mocker.patch("app.utils.storage.Storage.__init__", return_value=None)
        mock_storage_blob_exists = mocker.patch("app.utils.storage.Storage.blob_exists")
        mock_upload_blob = mocker.patch("app.utils.storage.Storage.upload_blob_from_base64string")
        yield
        mock_storage.assert_called_with('test-store')
        mock_upload_blob.assert_called_with(
            'test_filename.jpg', 'books/new-book.jpg', base64.b64encode(base64img.encode()))

    def it_creates_a_book(self, client, db_session, mock_storage):
        data = {
            'title': 'New book',
            'author': 'An Author',
            'description': 'Book description',
            'price': '5.00',
            'image_filename': 'test_filename.jpg',
            'image_data': base64img_encoded()
        }

        response = client.post(
            url_for('book.add_book'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201
        assert response.json['title'] == data['title']
        assert response.json['author'] == data['author']
        assert response.json['price'] == data['price']

    def it_doesnt_upload_book_image_if_storage_not_set(self, mocker, client, db_session):
        mock_storage = mocker.patch("app.utils.storage.Storage.__init__", return_value=None)
        mocker.patch.dict('app.application.config', {
            'STORAGE': 'Nonetest'
        })

        data = {
            'title': 'New book',
            'author': 'An Author',
            'description': 'Book description',
            'price': '5.00',
            'image_filename': 'test_filename.jpg',
            'image_data': base64img_encoded()
        }

        response = client.post(
            url_for('book.add_book'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 201

        json_events = json.loads(response.get_data(as_text=True))
        assert json_events["description"] == data["description"]
        assert not mock_storage.called


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
