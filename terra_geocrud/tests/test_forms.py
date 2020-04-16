from django.test import TestCase
from geostore.models import Layer, LayerExtraGeom

from terra_geocrud.models import ExtraLayerStyle
from .. import models
from ..forms import CrudViewForm, CrudPropertyForm, ExtraLayerStyleForm
from ..models import CrudViewProperty
from ..properties.schema import sync_layer_schema, sync_ui_schema


class ExtraLayerStyleFormTestCase(TestCase):
    def setUp(self) -> None:
        self.view_1 = models.CrudView.objects.create(name="View 1", order=0,
                                                     layer=Layer.objects.create(name=1))
        self.view_2 = models.CrudView.objects.create(name="View 2", order=1,
                                                     layer=Layer.objects.create(name=2))
        extra_layer = LayerExtraGeom.objects.create(layer=self.view_1.layer, title="extra")
        self.extra_style = ExtraLayerStyle.objects.create(crud_view=self.view_1, layer_extra_geom=extra_layer,
                                                          map_style={"test": "test"})
        self.prop_name = CrudViewProperty.objects.create(
            view=self.view_1, key="name",
            required=True,
            json_schema={'type': "string", "title": "Name"}
        )
        self.prop_age = CrudViewProperty.objects.create(
            view=self.view_2, key="age",
            json_schema={'type': "integer", "title": "Age"}
        )
        self.prop_country = CrudViewProperty.objects.create(
            view=self.view_2, key="country",
            json_schema={'type': "string", "title": "Country"}
        )
        sync_layer_schema(self.view_1)
        sync_ui_schema(self.view_1)
        sync_layer_schema(self.view_2)
        sync_ui_schema(self.view_2)

    def test_init(self):
        """ Available choices for a layer_extra_geom should match with its layer extra layer """
        form_1 = ExtraLayerStyleForm(instance=self.extra_style)
        self.assertListEqual(sorted(list(form_1.fields['layer_extra_geom'].queryset.values_list('pk',
                                                                                                flat=True))),
                             [self.extra_style.pk])


class CrudPropertyFormTestCase(TestCase):
    def setUp(self) -> None:
        self.view_1 = models.CrudView.objects.create(name="View 1", order=0,
                                                     layer=Layer.objects.create(name=1))
        self.prop_name = CrudViewProperty.objects.create(
            view=self.view_1, key="name",
            required=True,
            json_schema={'type': "string", "title": "Name"}
        )

    def test_available_groups(self):
        form = CrudPropertyForm(instance=self.prop_name)
        self.assertEqual(list(form.fields['group'].queryset), [])

    def test_key_is_avaible_at_creation(self):
        form = CrudPropertyForm()
        self.assertIsNone(form.fields['key'].widget.attrs.get('readonly'))

    def test_key_is_readonly_at_update(self):
        form = CrudPropertyForm(instance=self.prop_name)
        self.assertEqual(form.fields['key'].widget.attrs.get('readonly'), 'readonly')


class CrudViewFormTestCase(TestCase):
    def setUp(self) -> None:
        self.view_1 = models.CrudView.objects.create(name="View 1", order=0,
                                                     layer=Layer.objects.create(name=1))
        self.view_2 = models.CrudView.objects.create(name="View 2", order=1,
                                                     layer=Layer.objects.create(name=2))
        self.prop_name = CrudViewProperty.objects.create(
            view=self.view_1, key="name",
            required=True,
            json_schema={'type': "string", "title": "Name"}
        )
        self.prop_age = CrudViewProperty.objects.create(
            view=self.view_2, key="age",
            json_schema={'type': "integer", "title": "Age"}
        )
        self.prop_country = CrudViewProperty.objects.create(
            view=self.view_2, key="country",
            json_schema={'type': "string", "title": "Country"}
        )
        sync_layer_schema(self.view_1)
        sync_ui_schema(self.view_1)
        sync_layer_schema(self.view_2)
        sync_ui_schema(self.view_2)

    def test_available_properties_for_title(self):
        form_1 = CrudViewForm(instance=self.view_1)
        form_2 = CrudViewForm(instance=self.view_2)
        self.assertListEqual(sorted(list(form_1.fields['feature_title_property'].queryset.values_list('pk',
                                                                                                      flat=True))),
                             [self.prop_name.pk])
        self.assertListEqual(sorted(list(form_2.fields['feature_title_property'].queryset.values_list('pk',
                                                                                                      flat=True))),
                             sorted([self.prop_age.pk, self.prop_country.pk]))

    def test_available_properties_for_list(self):
        form_1 = CrudViewForm(instance=self.view_1)
        form_2 = CrudViewForm(instance=self.view_2)
        self.assertListEqual(sorted(list(form_1.fields['default_list_properties'].queryset.values_list('pk',
                                                                                                       flat=True))),
                             [self.prop_name.pk])
        self.assertListEqual(sorted(list(form_2.fields['default_list_properties'].queryset.values_list('pk',
                                                                                                       flat=True))),
                             sorted([self.prop_age.pk, self.prop_country.pk]))
