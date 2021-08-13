post_update_order_address_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for update order address",
    "type": "object",
    "properties": {
        "address_street": {"type": "string"},
        "address_city": {"type": "string"},
        "address_state": {"type": "string"},
        "address_postal_code": {"type": "string"},
        "address_country_code": {"type": "string"},
    },
    "required": ["address_street", "address_city", "address_postal_code", "address_country_code"]
}

post_update_order_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for update order",
    "type": "object",
    "properties": {
        "delivery_sent": {"type": "boolean"},
        "notes": {"type": "string"},
    },
    "required": ["delivery_sent", "notes"]
}
