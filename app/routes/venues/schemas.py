post_create_venue_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for creating venue",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "address": {"type": "string"},
        "directions": {"type": ["string", "null"]},
        "default": {"type": ["boolean", "false"]},
    },
    "required": ["name", "address"]
}

post_create_venues_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for creating venues",
    "type": "array",
    "items": {
        "type": "object",
        "$ref": "#/definitions/venue"
    },
    "definitions": {
        "venue": post_create_venue_schema
    }
}

post_import_venue_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing venue",
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "address": {"type": "string"},
        "tube": {"type": "string"},
        "bus": {"type": "string"},
    },
    "required": ["id", "name", "address"]
}

post_import_venues_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing venues",
    "type": "array",
    "items": {
        "type": "object",
        "$ref": "#/definitions/venue"
    },
    "definitions": {
        "venue": post_import_venue_schema
    }
}

post_update_venue_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for updating venue",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "address": {"type": "string"},
        "directions": {"type": ["string", "null"]},
        "default": {"type": ["boolean", "false"]},
    },
}
