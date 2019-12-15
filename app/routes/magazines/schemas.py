from app.schema_validation.definitions import number


post_import_magazine_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for import magazine",
    "type": "object",
    "properties": {
        "old_id": number,
        "title": {"type": "string"},
        "old_filename": {"type": "string"},
        "filename": {"type": "string"}
    },
    "required": ["old_id", "title", "old_filename", "filename"]
}


post_create_magazine_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for create magazine",
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "filename": {"type": "string"},
        "pdf_data": {"type": "string"},
    },
    "required": ["title", "filename", "pdf_data"]
}
