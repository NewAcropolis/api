from app.models import EMAIL_TYPES
from app.schema_validation.definitions import uuid, datetime, date


def email_types():
    pattern = '|'.join(EMAIL_TYPES)

    return {
        "type": "string",
        "pattern": pattern,
        "validationMessage": "is not an email type",
    }


post_create_email_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for creating email",
    "type": "object",
    "properties": {
        "event_id": uuid,
        "details": {"type": ["string", "null"]},
        "extra_txt": {"type": ["string", "null"]},
        "replace_all": {"type": "boolean"},
        "email_type": email_types(),
        "send_starts_at": date,
        "expires": date
    },
    "required": ["email_type"]
}


post_preview_email_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for preview email",
    "type": "object",
    "properties": {
        "event_id": uuid,
        "details": {"type": ["string", "null"]},
        "extra_txt": {"type": ["string", "null"]},
        "replace_all": {"type": "boolean"},
        "email_type": email_types()
    },
    "required": ["email_type"]
}


post_update_email_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for updating email",
    "type": "object",
    "properties": {
        "event_id": uuid,
        "details": {"type": ["string", "null"]},
        "extra_txt": {"type": ["string", "null"]},
        "replace_all": {"type": "boolean"},
        "email_type": email_types(),
        "send_starts_at": date,
        "expires": date,
        "reject_reason": {"type": ["string", "null"]},
    },
}


post_import_email_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing emails",
    "type": "object",
    "properties": {
        "id": {"format": "number", "type": "string"},
        "eventdetails": {"type": "string"},
        "extratxt": {"type": "string"},
        "replaceAll": {"type": "string"},
        "timestamp": datetime
    },
    "required": ["id", "timestamp"]
}


post_import_emails_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing emails",
    "type": "array",
    "items": {
        "type": "object",
        "$ref": "#/definitions/email"
    },
    "definitions": {
        "email": post_import_email_schema
    }
}


post_import_email_member_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing emails",
    "type": "object",
    "properties": {
        "id": {"format": "number", "type": "string"},
        "mailinglistid": {"format": "number", "type": "string"},
        "timestamp": datetime
    },
    "required": ["id", "mailinglistid", "timestamp"]
}


post_import_email_members_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing emails members",
    "type": "array",
    "items": {
        "type": "object",
        "$ref": "#/definitions/email_member"
    },
    "definitions": {
        "email_member": post_import_email_member_schema
    }
}


post_send_message_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for send message",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "email": {"format": "email", "type": "string"},
        "reason": {"type": "string"},
        "message": {"type": "string"}
    },
    "required": ["name", "email", "reason", "message"]
}
