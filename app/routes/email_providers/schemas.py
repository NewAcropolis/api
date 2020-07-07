post_create_email_provider_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for creating email provider",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "daily_limit": {"type": "integer"},
        "api_key": {"type": "string"},
        "api_url": {"type": "string"},
        "data_map": {"type": "string"},
        "pos": {"type": "integer"},
    },
    "required": ["name", "daily_limit", "api_key", "api_url", "data_map", "pos"]
}


post_update_email_provider_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for updating email provider",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "daily_limit": {"type": "integer"},
        "api_key": {"type": "string"},
        "api_url": {"type": "string"},
        "data_map": {"type": "string"},
        "pos": {"type": "integer"},
    },
}
