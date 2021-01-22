import tempfile

from django import forms
from django.conf import settings
from django.contrib.gis.forms import GeometryField
from django.contrib.gis.gdal import DataSource
from django.utils.translation import gettext as _
from geostore.models import FeatureExtraGeom, Layer

from . import models
from .models import CrudView, RoutingSettings


def parse_geometry_file(geom_file):
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(geom_file.read())
    temp.close()
    ds = DataSource(temp.name)
    geom = ds[0][0].geom.clone()
    geom.coord_dim = 2
    return geom.geos


class ExtraLayerStyleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # limit choices to available (linked by crud view / layer
            self.fields['layer_extra_geom'].queryset = self.instance.crud_view.layer.extra_geometries.all()

    class Meta:
        model = models.ExtraLayerStyle
        fields = "__all__"


class CrudPropertyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # limit choices to available (linked by crud view)
            self.fields['group'].queryset = self.instance.view.feature_display_groups.all()
            # unable to change property key after creation
            self.fields['key'].widget = forms.TextInput(attrs={'readonly': "readonly"})

    class Meta:
        model = models.CrudViewProperty
        fields = "__all__"


class CrudViewForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # limit choices to available (linked by crud view)
            self.fields['default_list_properties'].queryset = self.instance.list_available_properties.all()
            self.fields['feature_title_property'].queryset = self.instance.list_available_properties.all()
            # can only select a layer not used by a crud view
        else:
            self.fields['layer'].queryset = self.fields['layer'].queryset.\
                exclude(pk__in=CrudView.objects.values_list('layer_id', flat=True))

    class Meta:
        model = models.CrudView
        fields = "__all__"


class FeatureExtraGeomForm(forms.ModelForm):
    geom = GeometryField(required=False)
    geojson_file = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # limit choices to available (linked by crud view)
            self.fields['layer_extra_geom'].queryset = self.instance.feature.layer.extra_geometries.all()

    def clean(self):
        cleaned_data = super().clean()
        geojson_file = cleaned_data.get("geojson_file")
        geom = cleaned_data.get("geom")

        if not geojson_file and not geom:
            raise forms.ValidationError(
                _("You should define geometry with drawing or file.")
            )

    def save(self, commit=True):
        geojson_file = self.cleaned_data.get('geojson_file', None)

        if geojson_file:
            self.instance.geom = parse_geometry_file(geojson_file)
        return super().save(commit=commit)

    class Meta:
        model = FeatureExtraGeom
        fields = "__all__"


class RoutingSettingsForm(forms.ModelForm):
    layer = forms.ModelChoiceField(queryset=Layer.objects.filter(routable=True), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'geostore_routing' not in settings.INSTALLED_APPS:
            self.fields['layer'].widget = forms.HiddenInput()
            self.fields['provider'] = forms.ChoiceField(choices=RoutingSettings.CHOICES_EXTERNAL,
                                                        required=True)

    class Meta:
        model = RoutingSettings
        fields = "__all__"
