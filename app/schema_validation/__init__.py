import json

from jsonschema import (Draft4Validator, ValidationError, FormatChecker)

format_checker = FormatChecker()


def validate(json_to_validate, schema):
    validator = Draft4Validator(schema, format_checker=format_checker)
    errors = list(validator.iter_errors(json_to_validate))
    if errors.__len__() > 0:
        raise ValidationError(build_error_message(errors))
    return json_to_validate


@format_checker.checks('number')
def string_is_number(value):
    try:
        int(value)
        return True
    except Exception:
        return False


def build_error_message(errors):
    fields = []
    for e in errors:
        field = (
            "{} {}".format(e.path[0], e.schema['validationMessage'])
            if 'validationMessage' in e.schema else __format_message(e)
        )
        fields.append({"error": "ValidationError", "message": field})
    message = {
        "status_code": 400,
        "errors": unique_errors(fields)
    }

    return json.dumps(message)


def unique_errors(dups):
    unique = []
    for x in dups:
        if x not in unique:
            unique.append(x)
    return unique


def __format_message(e):
    def get_path(e):
        error_path = None
        try:
            # error_path = e.path.popleft()
            error_path = e.path.pop()
        finally:
            return error_path

    def get_error_message(e):
        error_message = str(e.cause) if e.cause else e.message
        return error_message.replace("'", '')

    path = get_path(e)
    message = get_error_message(e)
    if path:
        return "{} {}".format(path, message)
    else:
        return "{}".format(message)
