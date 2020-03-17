from app.schema_validation.definitions import uuid


post_import_member_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing member",
    "type": "object",
    "properties": {
        "id": {"format": "number", "type": "string"},
        "Name": {"type": "string"},
        "EmailAdd": {"format": "email", "type": ["string", "null"]},
        "Active": {"type": "string"},
        "CreationDate": {"format": "date-time", "type": ["string", "null"]},
        "Marketing": {"format": "number", "type": "string"},
        "IsMember": {"type": "string"},
        "LastUpdated": {"format": "date-time", "type": ["string", "null"]}
    },
    "required": ["id", "Name", "EmailAdd", "Active"]
}


post_import_members_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing members",
    "type": "array",
    "items": {
        "type": "object",
        "$ref": "#/definitions/member"
    },
    "definitions": {
        "member": post_import_member_schema
    }
}

post_subscribe_member_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for subscribing member",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "email": {"format": "email", "type": "string"},
        "marketing_id": uuid,
    },
    "required": ["name", "email", "marketing_id"]
}

post_update_member_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for update member",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "email": {"format": "email", "type": "string"},
    },
    "required": ["name", "email"]
}
