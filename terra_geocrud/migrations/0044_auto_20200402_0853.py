# Generated by Django 3.0.4 on 2020-04-02 08:53
from copy import deepcopy

from django.db import migrations


def create_properties(apps, schema_editor):
    CrudView = apps.get_model('terra_geocrud', 'CrudView')
    CrudViewProperty = apps.get_model('terra_geocrud', 'CrudViewProperty')
    FeaturePropertyDisplayGroup = apps.get_model('terra_geocrud', 'FeaturePropertyDisplayGroup')

    for view in CrudView.objects.all():
        json_schema = deepcopy(view.layer.schema)
        ui_schema = deepcopy(view.ui_schema)

        for key, value in json_schema.get('properties', {}).items():
            # find group by looking if key is declared in property
            group = FeaturePropertyDisplayGroup.objects.filter(crud_view=view, properties__contains=[key]).first()
            # find order by looking ui:order in ui schema
            order = 0
            try:
                order = ui_schema.get('ui:order', []).index(key)
            except ValueError:
                pass

            CrudViewProperty.objects.create(
                view=view,
                key=key,  # keep key
                json_schema=value,  # get value
                ui_schema=ui_schema.pop(key, {}),  # get ui schema else {}
                group=group,
                required=key in json_schema.get('required', []),
                order=order
            )


class Migration(migrations.Migration):

    dependencies = [
        ('terra_geocrud', '0043_auto_20200402_0852'),
    ]

    operations = [
        migrations.RunPython(create_properties),
    ]
