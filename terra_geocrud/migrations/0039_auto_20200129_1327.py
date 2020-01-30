# Generated by Django 2.2.9 on 2020-01-29 13:27

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion

from geostore.models import ArrayObjectProperty, LayerSchemaProperty


def move_ui_schema(apps, schema_editor):
    # We can't import Layer models directly as it may be a newer
    # version than this migration expects. We use the historical version.
    CrudView = apps.get_model('terra_geocrud', 'CrudView')
    UISchemaProperty = apps.get_model('terra_geocrud', 'UISchemaProperty')
    UIArraySchemaProperty = apps.get_model('terra_geocrud', 'UIArraySchemaProperty')
    LayerSchemaProperty = apps.get_model('geostore', 'LayerSchemaProperty')
    ArrayObjectProperty = apps.get_model('geostore', 'ArrayObjectProperty')

    for layer_schema in LayerSchemaProperty.objects.all():
        layer = layer_schema.layer
        view = layer.crud_view
        ui_schema = UISchemaProperty.objects.create(layer_schema_id=layer_schema.pk, crud_view=view,
                                                    order=0, schema={})
        for array_property in layer_schema.array_properties.all():
            UIArraySchemaProperty.objects.create(array_layer_schema_id=array_property.pk,
                                                 ui_schema_property=ui_schema,
                                                 order=0,
                                                 schema={})

    for view in CrudView.objects.all():
        ui_schema = view.ui_schema
        if ui_schema:
            order = ui_schema.pop("ui:order")
            for key, value in ui_schema.items():
                try:
                    layer_schema = LayerSchemaProperty.objects.get(layer_id=view.layer.pk, slug=key)
                except LayerSchemaProperty.DoesNotExist:
                    continue
                items = value.pop('items', {})
                ui_schema = UISchemaProperty.objects.get(layer_schema_id=layer_schema.pk, crud_view=view)
                ui_schema.schema = value
                ui_schema.save()

                if items:
                    order_items = items.pop("ui:order")
                    for key_items, value_items in items.items():
                        try:
                            array_layer_schema = ArrayObjectProperty.objects.get(array_property=layer_schema,
                                                                                 slug=key_items)
                        except ArrayObjectProperty.DoesNotExist:
                            continue
                        ui_array_schema = UIArraySchemaProperty.objects.get(array_layer_schema_id=array_layer_schema.pk,
                                                                            ui_schema_property=ui_schema)
                        ui_array_schema.schema = value_items
                        ui_array_schema.save()
                    for element_order in order_items:
                        array_layer_schema = ArrayObjectProperty.objects.get(array_property=layer_schema,
                                                                             slug=element_order)
                        ui_array_schema = UIArraySchemaProperty.objects.get(array_layer_schema_id=array_layer_schema.pk,
                                                                            ui_schema_property=ui_schema)
                        try:
                            ui_array_schema.order = order.index(element_order) + 1
                            ui_array_schema.save()
                        except ValueError:
                            continue

            for element_order in order:
                try:
                    layer_schema = LayerSchemaProperty.objects.get(layer_id=view.layer.pk, slug=element_order)
                except LayerSchemaProperty.DoesNotExist:
                    continue
                ui_schema = UISchemaProperty.objects.get(layer_schema_id=layer_schema.pk, crud_view=view)
                try:
                    ui_schema.order = order.index(element_order) + 1
                    ui_schema.save()
                except ValueError:
                    continue


class Migration(migrations.Migration):

    dependencies = [
        ('geostore', '0041_auto_20200128_1414'),
        ('terra_geocrud', '0038_move_data_title_property'),
    ]

    operations = [
        migrations.CreateModel(
            name='UISchemaProperty',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('schema', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, help_text='Custom ui schema')),
                ('order', models.PositiveSmallIntegerField(db_index=True, default=0)),
                ('crud_view', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ui_schema_properties', to='terra_geocrud.CrudView')),
                ('layer_schema', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='ui_schema_property', to='geostore.LayerSchemaProperty')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UIArraySchemaProperty',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('schema', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, help_text='Custom ui schema')),
                ('order', models.PositiveSmallIntegerField(db_index=True, default=0)),
                ('array_layer_schema', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='ui_array_schema', to='geostore.ArrayObjectProperty')),
                ('ui_schema_property', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ui_array_properties', to='terra_geocrud.UISchemaProperty')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RunPython(move_ui_schema),
        migrations.RemoveField(
            model_name='crudview',
            name='ui_schema',
        ),
    ]
