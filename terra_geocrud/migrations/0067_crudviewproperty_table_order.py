# Generated by Django 3.2.7 on 2021-09-20 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('terra_geocrud', '0066_auto_20210618_0901'),
    ]

    operations = [
        migrations.AddField(
            model_name='crudviewproperty',
            name='table_order',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
