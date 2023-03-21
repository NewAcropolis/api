uuid = {
    "type": "string",
    "pattern": "^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$",
    "validationMessage": "is not a valid UUID",
}

datetime = {
    "type": "string",
    "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}(:[0-9]{2})?$",
    "validationMessage": "is not a datetime in format YYYY-MM-DD HH:MM(:SS)?",
}

date = {
    "type": "string",
    "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
    "validationMessage": "is not a date in format YYYY-MM-DD",
}

time = {
    "type": "string",
    "pattern": "^([0-9]{2}:[0-9]{2}(:[0-9]{2})?)?$",
    "validationMessage": "is not a time in format HH:MM(:SS)?",
}

money = {
    "type": "string",
    "pattern": "^(0|([1-9]+[0-9]*))(.[0-9]{1,2})?$",
    "description": "A Monetary Amount",
}

number = {
    "type": "string",
    "pattern": "^[0-9]+$",
    "validationMessage": "is not a number",
}

state = {
    "type": "string",
    "pattern": "draft|ready|approved|rejected",
    "validationMessage": "is not a recognised state",
}


def nullable(schema_type):
    return {
        "oneOf": [
            {"type": "null"},
            {
                "format": schema_type,
                "type": "string"
            }
        ]
    }  # pragma: no cover
