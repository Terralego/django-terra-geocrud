from django.core.exceptions import ValidationError
from django.test import TestCase

from terra_geocrud.validators import validate_schema_property, validate_function_path


class ValidateFunctionPathTestCase(TestCase):
    def test_validator_with_right_function_path(self):
        with self.assertRaises(ValidationError):
            validate_function_path('not_available')


class ValidateSchemaPropertyTestCase(TestCase):
    def test_validator_with_right_schema(self):
        self.assertIsNotNone(
            validate_schema_property({"type": "string", "title": "Test"})
        )

    def test_validator_with_wrong_schema(self):
        with self.assertRaises(ValidationError):
            validate_schema_property({"type": "unknown"})
