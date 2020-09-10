try:
    from django.db.models import JSONField
except ImportError:  # TODO: Remove when dropping Django releases < 3.1
    from django.contrib.postgres.fields import JSONField
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('terra_geocrud', '0019_auto_20190927_1349'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='featurepropertydisplaygroup',
            options={'ordering': ('order', 'label'), 'verbose_name': 'Feature properties display group', 'verbose_name_plural': 'Feature properties display groups'},
        ),
        migrations.AlterField(
            model_name='crudgroupview',
            name='name',
            field=models.CharField(help_text='Display name in left menu', max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='crudgroupview',
            name='order',
            field=models.PositiveSmallIntegerField(help_text='Order entry in left menu'),
        ),
        migrations.AlterField(
            model_name='crudgroupview',
            name='pictogram',
            field=models.ImageField(blank=True, help_text='Picto displayed in left menu', null=True, upload_to='crud/groups/pictograms'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='group',
            field=models.ForeignKey(blank=True, help_text='Group this entry in left menu', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='crud_views', to='terra_geocrud.CrudGroupView'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='map_style',
            field=JSONField(blank=True, default=dict, help_text='Custom mapbox style for this entry'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='name',
            field=models.CharField(help_text='Display name in left menu', max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='order',
            field=models.PositiveSmallIntegerField(help_text='Order entry in left menu'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='pictogram',
            field=models.ImageField(blank=True, help_text='Picto displayed in left menu', null=True, upload_to='crud/views/pictograms'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='templates',
            field=models.ManyToManyField(blank=True, help_text='Available templates for layer features document generation', related_name='crud_views', to='template_model.Template'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='ui_schema',
            field=JSONField(blank=True, default=dict, help_text='Custom ui:schema style for this entry. https://react-jsonschema-form.readthedocs.io/en/latest/form-customization/'),
        ),
    ]
