from importlib import import_module

from django.core.exceptions import ValidationError

from geostore.validators import validate_json_schema


def validate_schema_property(value):
    """ check if schema property is valid """
    json_schema = {
        "properties": {
            "temp": value
        }
    }
    return validate_json_schema(json_schema)


def validate_function_path(value):
    if value:
        module = import_module('.functions', 'terra_geocrud')
        if not hasattr(module, value):
            raise ValidationError(message="function does not exist")
    return value
