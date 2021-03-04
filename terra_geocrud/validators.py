from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string

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
        try:
            import_string(value)
        except ImportError:
            raise ValidationError(message=f"function {value} does not exist")
    return value
