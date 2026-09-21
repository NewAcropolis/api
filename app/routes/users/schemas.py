

post_create_user_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for creating user",
    "type": "object",
    "properties": {
        'email': {"type": "string"},
        'name': {"type": "string"},
        'active': {"type": "boolean"},
        'access_area': {"type": "string"},
    },
    "required": ['email']
}

post_update_user_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for updating user",
    "type": "object",
    "properties": {
        'name': {"type": "string"},
        'active': {"type": "boolean"},
        'access_area': {"type": "string"},
        'last_login': {"type": "date-time"},
        'session_id': {"type": "string"},
        'ip': {"type": "string"},
    },
    "required": []
}
