import pytest

import json
from jsonschema import ValidationError

from app.schema_validation.definitions import uuid, datetime
from app.schema_validation import validate

test_uuid_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema testing uuid",
    "type": "object",
    "properties": {
        'test': {"type": "string"},
        'id': uuid,
    },
    "required": ["test"]
}

test_number_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "POST schema testing uuid",
    "type": "object",
    "properties": {
        "id": {
            "oneOf": [
                {"type": "null"},
                {
                    "format": "number",
                    "type": "string"
                }
            ]
        },
    },
    "required": ["id"]
}


class WhenProcessingRequests(object):
    def it_validates_uuid_requests(self, sample_uuid):
        data = {
            "test": "something",
            "id": sample_uuid
        }
        validate(data, test_uuid_schema)

    def it_validates_number_requests(self):
        data = {
            "id": "100"
        }
        validate(data, test_number_schema)

    def it_errors_on_invalid_number_requests(self):
        data = {
            "id": "x"
        }
        with pytest.raises(expected_exception=ValidationError) as e:
            validate(data, test_number_schema)

        json_err = json.loads(str(e.value))

        assert {
            "message": "id x is not valid under any of the given schemas",
            "error": "ValidationError"
        } in json_err['errors']
