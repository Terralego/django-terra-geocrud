# Generated by Django 2.1.11 on 2019-08-30 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('template_model', '0001_initial'),
        ('terra_geocrud', '0009_auto_20190830_1018'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='crudview',
            name='template',
        ),
        migrations.AddField(
            model_name='crudview',
            name='templates',
            field=models.ManyToManyField(blank=True, null=True, related_name='crud_views', to='template_model.Template'),
        ),
    ]
