# Generated by Django 3.1.2 on 2020-10-21 12:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('terra_geocrud', '0057_crudviewproperty_include_in_tile'),
    ]

    operations = [
        migrations.CreateModel(
            name='PropertyEnum',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=250)),
                ('pictogram', models.ImageField(blank=True, help_text='Picto. associated to value.', null=True, upload_to='terra_geocrud/enums/pictograms')),
                ('property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='terra_geocrud.crudviewproperty')),
            ],
            options={
                'unique_together': {('value', 'property')},
            },
        ),
    ]
