try:
    from django.db.models import JSONField
except ImportError:  # TODO: Remove when dropping Django releases < 3.1
    from django.contrib.postgres.fields import JSONField
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('geostore', '0041_auto_20200625_1515'),
        ('template_model', '0004_auto_20190916_0913'),
        ('terra_geocrud', '0055_auto_20200603_1150'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crudgroupview',
            name='name',
            field=models.CharField(help_text='Display name in left menu', max_length=100, unique=True, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='crudgroupview',
            name='order',
            field=models.PositiveSmallIntegerField(db_index=True, help_text='Order entry in left menu', verbose_name='Order'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='default_list_properties',
            field=models.ManyToManyField(blank=True, help_text='Schema properties used in API list by default.', related_name='used_by_list', to='terra_geocrud.CrudViewProperty', verbose_name='Properties in feature list'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='feature_title_property',
            field=models.ForeignKey(blank=True, help_text='Schema property used to define feature title.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='used_by_title', to='terra_geocrud.crudviewproperty', verbose_name='Title property'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='group',
            field=models.ForeignKey(blank=True, help_text='Group this entry in left menu', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='crud_views', to='terra_geocrud.crudgroupview', verbose_name='Group'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='layer',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='crud_view', to='geostore.layer', verbose_name='Layer'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='map_style',
            field=JSONField(blank=True, default=dict, help_text='Custom mapbox style for this entry', verbose_name='Map style'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='name',
            field=models.CharField(help_text='Display name in left menu', max_length=100, unique=True, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='object_name',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Singular object name'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='object_name_plural',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Plural object name'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='order',
            field=models.PositiveSmallIntegerField(db_index=True, help_text='Order entry in left menu', verbose_name='Order'),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='templates',
            field=models.ManyToManyField(blank=True, help_text='Available templates for layer features document generation', related_name='crud_views', to='template_model.Template', verbose_name='Document templates'),
        ),
    ]
