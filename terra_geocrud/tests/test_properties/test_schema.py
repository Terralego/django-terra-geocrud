from django.test import TestCase
from geostore.models import Feature

from terra_geocrud.models import CrudViewProperty
from terra_geocrud.properties.schema import sync_layer_schema, sync_ui_schema, clean_properties_not_in_schema_or_null, \
    sync_properties_in_tiles
from terra_geocrud.tests.factories import CrudViewFactory


class CleanPropertiesNotInSchemaOrNullTestCase(TestCase):
    def setUp(self) -> None:
        self.view = CrudViewFactory()
        self.prop_name = CrudViewProperty.objects.create(
            view=self.view, key="name",
            required=True,
            json_schema={'type': "string", "title": "Name"}
        )
        self.prop_age = CrudViewProperty.objects.create(
            view=self.view, key="age",
            json_schema={'type': "integer", "title": "Age"}
        )
        self.prop_country = CrudViewProperty.objects.create(
            view=self.view, key="country",
            json_schema={'type': "string", "title": "Country"}
        )
        sync_layer_schema(self.view)
        sync_ui_schema(self.view)
        self.feature = Feature.objects.create(layer=self.view.layer,
                                              geom='POINT(0 0)',
                                              properties={
                                                  "name": None,
                                                  "age": 15,
                                                  "country": "Country"
                                              })

    def test_value_is_removed_if_null(self):
        # clean
        clean_properties_not_in_schema_or_null(self.view)
        # key not in properties anymore
        self.feature.refresh_from_db()
        self.assertNotIn('name', self.feature.properties)

    def test_value_is_removed_if_property_deleted(self):
        self.prop_age.delete()
        sync_layer_schema(self.view)
        sync_ui_schema(self.view)
        self.feature.refresh_from_db()
        self.assertIn('age', self.feature.properties)
        clean_properties_not_in_schema_or_null(self.view)
        self.feature.refresh_from_db()
        self.assertNotIn('age', self.feature.properties)


class PropertiesInTilesTestCase(TestCase):
    def setUp(self) -> None:
        self.view = CrudViewFactory()
        self.prop_name = CrudViewProperty.objects.create(
            view=self.view, key="name",
            required=True,
            json_schema={'type': "string", "title": "Name"},
            include_in_tile=True
        )
        self.prop_age = CrudViewProperty.objects.create(
            view=self.view, key="age",
            json_schema={'type': "integer", "title": "Age"}
        )
        self.prop_country = CrudViewProperty.objects.create(
            view=self.view, key="country",
            json_schema={'type': "string", "title": "Country"}
        )
        sync_layer_schema(self.view)
        sync_ui_schema(self.view)
        sync_properties_in_tiles(self.view)

    def test_value_is_present(self):
        self.assertDictEqual(self.view.layer.settings, {"tiles": {"properties_filter": ["name"]}})

    def test_value_is_removed_when_false(self):
        # clean
        self.prop_name.include_in_tile = False
        self.prop_name.save()
        sync_properties_in_tiles(self.view)
        # key not in properties anymore
        self.assertDictEqual(self.view.layer.settings, {"tiles": {"properties_filter": None}})
