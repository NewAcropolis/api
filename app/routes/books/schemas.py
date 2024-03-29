from app.schema_validation.definitions import uuid, number, money


post_import_book_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing book",
    "type": "object",
    "properties": {
        "id": {
            "format": "number",
            "type": "string"
        },
        'Title': {"type": "string"},
        'Author': {"type": "string"},
        'Price': money,
        'BuyCode': {"type": "string"},
        'ImageFilename': {"type": "string"},
    },
    "required": ["id", "Title", "Author"]
}

post_import_books_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing books",
    "type": "array",
    "items": {
        "type": "object",
        "$ref": "#/definitions/book"
    },
    "definitions": {
        "book": post_import_book_schema
    }
}

post_update_book_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for updating book",
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        'title': {"type": "string"},
        'author': {"type": "string"},
        'price': money,
        'buy_code': {"type": "string"},
        'image_filename': {"type": "string"},
        "image_data": {
            "type": ["string", "null"],
            "media": {
                "binaryEncoding": "base64",
                "type": "image/png"
            }
        }
    }
}

post_create_book_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for creating a book",
    "type": "object",
    "properties": {
        'title': {"type": "string"},
        'author': {"type": "string"},
        'description': {"type": "string"},
        'price': money,
        'image_filename': {"type": "string"},
        "image_data": {
            "type": ["string", "null"],
            "media": {
                "binaryEncoding": "base64",
                "type": "image/png"
            }
        }
    },
    "required": ["title", "author", "price", "image_filename", "image_data"]
}
