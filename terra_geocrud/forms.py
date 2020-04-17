from django import forms

from . import models


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

    class Meta:
        model = models.CrudView
        fields = "__all__"
