from app.schema_validation.definitions import uuid, number


post_import_article_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing article",
    "type": "object",
    "properties": {
        "id": {
            "format": "number",
            "type": "string"
        },
        'title': {"type": "string"},
        'author': {"type": "string"},
        'content': {"type": "string"},
        'entrydate': {"type": "string"},
    },
    "required": ["id", "title", "content"]
}

post_import_articles_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing articles",
    "type": "array",
    "items": {
        "type": "object",
        "$ref": "#/definitions/article"
    },
    "definitions": {
        "article": post_import_article_schema
    }
}
