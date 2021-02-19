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
        val = value.split('.')
        function = val[-1]
        module_path = '.'.join(val[:-1])
        if not module_path:
            raise ValidationError(message="function should be in a package")
        module = import_module(module_path)
        if not hasattr(module, function):
            raise ValidationError(message="function does not exist")
    return value
