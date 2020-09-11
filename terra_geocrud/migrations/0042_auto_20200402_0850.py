try:
    from django.db.models import JSONField
except ImportError:  # TODO: Remove when dropping Django releases < 3.1
    from django.contrib.postgres.fields import JSONField
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('terra_geocrud', '0041_auto_20200325_1351'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crudview',
            name='object_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='object_name_plural',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.CreateModel(
            name='CrudViewProperty',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.SlugField()),
                ('json_schema', JSONField(default=dict)),
                ('ui_schema', JSONField(blank=True, default=dict)),
                ('required', models.BooleanField(default=False)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='group_properties', to='terra_geocrud.FeaturePropertyDisplayGroup')),
                ('view', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='properties', to='terra_geocrud.CrudView')),
            ],
            options={
                'ordering': ('view', 'order'),
                'unique_together': {('view', 'key'), },
            },
        ),
    ]
