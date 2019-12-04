from copy import deepcopy

from django.core.exceptions import ValidationError
from django.utils.functional import cached_property


class FormSchemaMixin:
    def clean(self):
        # verify properties in default_list_properties exist
        unexpected_properties = list(set(self.default_list_properties) - set(self.list_available_properties))
        if unexpected_properties:
            raise ValidationError(f'Properties should exists for feature list : {unexpected_properties}')
        # verify feature_title_property exists
        if self.feature_title_property and self.feature_title_property not in self.properties:
            raise ValidationError(f'Property should exists for feature title : {self.feature_title_property}')

    @cached_property
    def grouped_form_schema(self):
        original_schema = deepcopy(self.layer.schema)
        generated_schema = deepcopy(original_schema)
        groups = self.feature_display_groups.all()
        processed_properties = []
        generated_schema['properties'] = {}

        for group in groups:
            # group properties by sub object, then add other properties
            generated_schema['properties'][group.slug] = group.form_schema
            processed_properties += list(group.properties)
            for prop in group.properties:
                try:
                    generated_schema.get('required', []).remove(prop)
                except ValueError:
                    pass
        # add default other properties
        remained_properties = list(set(self.properties) - set(processed_properties))
        for prop in remained_properties:
            generated_schema['properties'][prop] = original_schema['properties'][prop]

        return generated_schema

    @cached_property
    def grouped_ui_schema(self):
        """
        Original ui_schema is recomposed with grouped properties
        """
        ui_schema = deepcopy(self.ui_schema)

        groups = self.feature_display_groups.all()
        for group in groups:
            # each field defined in ui schema should be placed in group key
            ui_schema[group.slug] = {'ui:order': []}

            for prop in group.properties:
                # get original definition
                original_def = ui_schema.pop(prop, None)
                if original_def:
                    ui_schema[group.slug][prop] = original_def

                # if original prop in ui:order
                if prop in ui_schema.get('ui:order', []):
                    ui_schema.get('ui:order').remove(prop)
                    ui_schema[group.slug]['ui:order'] += [prop]

            # finish by adding '*' in all cases (security)
            ui_schema[group.slug]['ui:order'] += ['*']
        if groups:
            ui_schema['ui:order'] = list(groups.values_list('slug', flat=True)) + ['*']
        return ui_schema

    @cached_property
    def properties(self):
        return sorted(list(self.layer.layer_properties.keys())) if self.layer else []

    @cached_property
    def list_available_properties(self):
        """ exclude some properties in list (some arrays, data-url, html fields)"""
        properties = []

        for prop in self.properties:
            # exclude format 'data-url', array if final data is object, and textarea / rte fields
            if (self.layer.schema.get('properties', {}).get(prop).get('format') != 'data-url') and (
                    self.layer.schema.get('properties', {}).get(prop).get('type') != 'array'
                    or self.layer.schema.get('properties', {}).get(prop).get('items', {}).get('type') != 'object') \
                    and (self.ui_schema.get(prop, {}).get('ui:widget') != 'textarea'
                         and self.ui_schema.get(prop, {}).get('ui:field') != 'rte'):
                properties.append(prop)
        return properties
