from app.schema_validation.definitions import number


post_create_event_type_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for creating event_type",
    "type": "object",
    "properties": {
        "event_type": {"type": "string"},
        "event_desc": {"type": ["string", "null"]},
        "event_filename": {"type": ["string", "null"]},
        "duration": {"type": ["integer", "null"]},
        "repeat": {"type": ["integer", "null"]},
        "repeat_interval": {"type": ["integer", "null"]},
    },
    "required": ["event_type"]
}


post_update_event_type_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for updating event_type",
    "type": "object",
    "properties": {
        "event_type": {"type": "string"},
        "event_desc": {"type": ["string", "null"]},
        "event_filename": {"type": ["string", "null"]},
        "duration": {"type": ["integer", "null"]},
        "repeat": {"type": ["integer", "null"]},
        "repeat_interval": {"type": ["integer", "null"]},
    },
}


# {"id":"1","EventType":"Talk","Fees":"5","ConcFees":"3","EventDesc":"","EventFilename":null}

post_import_event_type_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing event type",
    "type": "object",
    "properties": {
        "id": number,
        "EventType": {"type": "string"},
        # "Fees": number,         # ignore
        # "ConcFees": number,     # ignore
        "EventDesc": {"type": ["string", "null"]},
        "EventFilename": {"type": ["string", "null"]},
    },
    "required": ["id", "EventType"]
}

post_import_event_types_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing event types",
    "type": "array",
    "items": {
        "type": "object",
        "$ref": "#/definitions/event_type"
    },
    "definitions": {
        "event_type": post_import_event_type_schema
    }
}
