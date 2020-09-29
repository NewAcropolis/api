from flask import json, url_for
from tests.conftest import create_authorization_header


sample_books = [{
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
            data=json.dumps(sample_books),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_books = json.loads(response.get_data(as_text=True))['books']
        assert len(json_books) == len(sample_books)
        for i in range(0, len(sample_books) - 1):
            assert json_books[i]["old_id"] == int(sample_books[i]["id"])
            assert json_books[i]["title"] == sample_books[i]["Title"]
            assert json_books[i]["author"] == sample_books[i]["Author"]

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

        sample_books.extend(duplicate_book)

        response = client.post(
            url_for('books.import_books'),
            data=json.dumps(sample_books),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_books = json.loads(response.get_data(as_text=True))['books']
        assert len(json_books) == len(sample_books) - 1  # don't add in duplicate book
        for i in range(0, len(sample_books) - 1):
            assert json_books[i]["old_id"] == int(sample_books[i]["id"])
            assert json_books[i]["title"] == sample_books[i]["Title"]
            assert json_books[i]["author"] == sample_books[i]["Author"]
