# Generated by Django 2.2.6 on 2019-10-14 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('terra_geocrud', '0025_auto_20191008_1023'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='crudview',
            options={'ordering': ('order',), 'permissions': [('can_manage_views', 'Can create / edit / delete views / groups and associated layers.'), ('can_view_feature', 'Can read feature detail.'), ('can_add_feature', 'Can create feature'), ('can_change_feature', 'Can change feature'), ('can_delete_feature', 'Can delete feature')], 'verbose_name': 'View', 'verbose_name_plural': 'Views'},
        ),
        migrations.AlterField(
            model_name='propertydisplayrendering',
            name='widget',
            field=models.CharField(choices=[('terra_geocrud.properties.widgets.DataUrlToImgWidget', 'DataUrlToImgWidget'), ('terra_geocrud.properties.widgets.DateFormatWidget', 'DateFormatWidget'), ('terra_geocrud.properties.widgets.FileAhrefWidget', 'FileAhrefWidget')], max_length=255),
        ),
    ]
