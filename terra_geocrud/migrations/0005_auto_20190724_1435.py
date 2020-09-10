try:
    from django.db.models import JSONField
except ImportError:  # TODO: Remove when dropping Django releases < 3.1
    from django.contrib.postgres.fields import JSONField
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('terra_geocrud', '0004_auto_20190724_0906'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crudview',
            name='map_style',
            field=JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='crudview',
            name='pictogram',
            field=models.ImageField(blank=True, null=True, upload_to='crud/views/pictograms'),
        ),
    ]
