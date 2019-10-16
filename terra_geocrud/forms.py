from django import forms
from django.db import transaction
from django.utils.text import slugify
from geostore.models import Layer

from terra_geocrud.widgets import JSONEditorWidget
from terra_geocrud.models import CrudView

from geostore import GeometryTypes


class CrudViewAdminForm(forms.ModelForm):
    layer_schema = forms.CharField(widget=JSONEditorWidget)
    layer_geom_type = forms.TypedChoiceField(choices=GeometryTypes.choices(), coerce=int)
    layer_settings = forms.CharField(widget=JSONEditorWidget)

    class Meta:
        model = CrudView
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            print(self.instance.layer)
            # set initial from layer
            self.fields['layer_schema'].initial = self.instance.layer.schema
            self.fields['layer_geom_type'].initial = self.instance.layer.geom_type
            self.fields['layer_settings'].initial = self.instance.layer.settings

    def save(self, commit=True):
        if self.instance.pk:
            layer = self.instance.layer
            layer.schema = self.cleaned_data['layer_schema']
            layer.settings = self.cleaned_data['layer_settings']
            layer.geom_type = self.cleaned_data['layer_geom_type']
            layer.save()
        else:
            layer = Layer.objects.create(name=slugify(self.instance.name),
                                         schema=self.cleaned_data['layer_schema'],
                                         settings=self.cleaned_data['layer_settings'],
                                         geom_type=self.cleaned_data['layer_geom_type'])
            self.instance.layer = layer
        super(CrudViewAdminForm, self).save(commit=commit)
