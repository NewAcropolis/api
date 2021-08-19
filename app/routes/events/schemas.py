from app.schema_validation.definitions import datetime, number, uuid, nullable, time


event_date_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for event_date",
    "type": "object",
    "properties": {
        "event_date": datetime,
        "end_time": time,
        "speakers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "speaker_id": uuid,
                }
            },
        },
    },
    "required": ["event_date"]
}


reject_reason_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for reject_reason",
    "type": "object",
    "properties": {
        "reason": {"type": "string", "minLength": 3},
        "resolved": {"type": "boolean"},
        "created_by": uuid
    },
    "required": ["reason"]
}


post_create_event_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for creating event",
    "type": "object",
    "properties": {
        "event_type_id": uuid,
        "title": {"type": "string"},
        "sub_title": {"type": ["string", "null"]},
        "description": {"type": "string"},
        "booking_code": {"type": ["string", "null"]},
        "image_filename": {"type": ["string", "null"]},
        "image_data": {
            "type": ["string", "null"],
            "media": {
                "binaryEncoding": "base64",
                "type": "image/png"
            }
        },
        "fee": {"type": ["integer", "null"]},
        "conc_fee": {"type": ["integer", "null"]},
        "multi_day_fee": {"type": ["integer", "null"]},
        "multi_day_conc_fee": {"type": ["integer", "null"]},
        "event_dates": {
            "type": "array",
            "items": {
                "type": "object",
                "$ref": "#/definitions/event_date",
            },
            "minItems": 1,
        },
        "venue_id": {"type": "string"},
        "state": {"type": ["string", "null"]},
        "remote_access": {"type": "string"},
        "remote_pw": {"type": "string"},
    },
    "definitions": {
        "type": "object",
        "event_date": event_date_schema,
    },
    "required": ["event_type_id", "title", "description", "event_dates", "venue_id"]
}


post_import_event_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing event",
    "type": "object",
    "properties": {
        "id": {
            "format": "number",
            "type": "string"
        },
        "BookingCode": {"type": "string"},
        "MemberPay": {"type": "string"},                    # unused
        "Approved": {"type": "string"},                     # unused
        "Type": {
            "format": "number",
            "type": "string"
        },
        "Title": {"type": "string"},
        "SubTitle": {"type": "string"},
        "Description": {"type": "string"},
        "venue": {
            "format": "number",
            "type": "string"
        },
        "Speaker": {"type": "string"},
        "MultiDayFee": {
            "oneOf": [
                {"type": "null"},
                {
                    "format": "number",
                    "type": "string"
                }
            ]
        },
        "MultiDayConcFee": {
            "oneOf": [
                {"type": "null"},
                {
                    "format": "number",
                    "type": "string"
                }
            ]
        },
        "StartDate": {
            "format": "date-time",
            "type": "string",
            "description": "Date+time event"
        },
        "StartDate2": {
            "format": "date-time",
            "type": ["string", "null"],
            "description": "Date+time event 2"
        },
        "StartDate3": {
            "format": "date-time",
            "type": ["string", "null"],
            "description": "Date+time event 3"
        },
        "StartDate4": {
            "format": "date-time",
            "type": ["string", "null"],
            "description": "Date+time event 4"
        },
        "EndDate": {
            "format": "date-time",
            "type": ["string", "null"],
            "description": "End date+time event"
        },
        "Duration": {
            "format": "number",
            "type": "string"
        },
        "Fee": {
            "oneOf": [
                {"type": "null"},
                {
                    "format": "number",
                    "type": "string"
                }
            ]
        },
        "ConcFee": {
            "oneOf": [
                {"type": "null"},
                {
                    "format": "number",
                    "type": "string"
                }
            ]
        },
        "Pub-First-Number": {"type": ["string", "null"]},   # unused
        "Mem-SignOn-Number": {"type": ["string", "null"]},  # unused
        "ImageFilename": {"type": "string"},
        "WebLink": {"type": "string"},                      # unused
        "LinkText": {"type": ["string", "null"]},                     # unused
        "MembersOnly": {"type": "string"},                  # unused
        "RegisterStartOnly": {"type": "string"},            # unused
        "SoldOut": {"type": ["string", "null"]},            # unused
    },
    "required": ["id", "Type", "Title"]
}

post_import_events_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for importing events",
    "type": "array",
    "items": {
        "type": "object",
        "$ref": "#/definitions/event"
    },
    "definitions": {
        "event": post_import_event_schema
    }
}

post_update_event_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema for updating event",
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "sub_title": {"type": ["string", "null"]},
        "description": {"type": "string"},
        "booking_code": {"type": ["string", "null"]},
        "image_filename": {"type": ["string", "null"]},
        "image_data": {
            "type": ["string", "null"],
            "media": {
                "binaryEncoding": "base64",
                "type": "image/png"
            }
        },
        "fee": {"type": ["integer", "null"]},
        "conc_fee": {"type": ["integer", "null"]},
        "multi_day_fee": {"type": ["integer", "null"]},
        "multi_day_conc_fee": {"type": ["integer", "null"]},
        "event_dates": {
            "type": "array",
            "items": {
                "type": "object",
                "$ref": "#/definitions/event_date",
            },
        },
        "reject_reasons": {
            "type": "array",
            "items": {
                "type": "object",
                "$ref": "#/definitions/reject_reason",
            },
        },
        "venue_id": {"type": "string"},
        "state": {"type": ["string", "null"]},
    },
    "definitions": {
        "type": "object",
        "event_date": event_date_schema,
        "reject_reason": reject_reason_schema
    },
}
