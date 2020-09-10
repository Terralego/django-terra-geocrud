try:
    from django.db.models import JSONField
except ImportError:  # TODO: Remove when dropping Django releases < 3.1
    from django.contrib.postgres.fields import JSONField
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('geostore', '0033_featureextrageom_layerextrageom'),
        ('terra_geocrud', '0032_crudview_visible'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExtraLayerStyle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('map_style', JSONField(help_text='Custom mapbox style for this entry')),
                ('crud_view', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='extra_layer_style', to='terra_geocrud.CrudView')),
                ('layer_extra_geom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='style', to='geostore.LayerExtraGeom')),
            ],
            options={
                'verbose_name': 'ExtraLayer style',
                'verbose_name_plural': 'ExtraLayer styles',
                'unique_together': {('crud_view', 'layer_extra_geom')},
            },
        ),
    ]
