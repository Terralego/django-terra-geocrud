try:
    from django.db.models import JSONField
except ImportError:  # TODO: Remove when dropping Django releases < 3.1
    from django.contrib.postgres.fields import JSONField
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('geostore', '0026_auto_20190613_1529'),
    ]

    operations = [
        migrations.CreateModel(
            name='CrudGroupView',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('order', models.PositiveSmallIntegerField(unique=True)),
                ('pictogram', models.ImageField(upload_to='crud/groups/pictograms')),
            ],
            options={
                'verbose_name': 'Group',
                'verbose_name_plural': 'Groups',
                'ordering': ('order',),
            },
        ),
        migrations.CreateModel(
            name='CrudView',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('order', models.PositiveSmallIntegerField(unique=True)),
                ('pictogram', models.ImageField(upload_to='crud/views/pictograms')),
                ('map_style', JSONField(default=dict)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='terra_geocrud.CrudGroupView')),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='geostore.Layer')),
            ],
            options={
                'verbose_name': 'View',
                'verbose_name_plural': 'Views',
                'ordering': ('order',),
            },
        ),
    ]
