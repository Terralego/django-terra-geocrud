# Generated by Django 3.1.2 on 2020-10-21 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('terra_geocrud', '0056_auto_20200915_0922'),
    ]

    operations = [
        migrations.AddField(
            model_name='crudviewproperty',
            name='include_in_tile',
            field=models.BooleanField(default=False),
        ),
    ]
