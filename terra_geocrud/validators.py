from geostore.validators import validate_json_schema


def validate_schema_property(value):
    """ check if schema property is valid """
    json_schema = {
        "properties": {
            "temp": value
        }
    }
    validate_json_schema(json_schema)
