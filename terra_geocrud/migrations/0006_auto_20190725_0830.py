try:
    from django.db.models import JSONField
except ImportError:  # TODO: Remove when dropping Django releases < 3.1
    from django.contrib.postgres.fields import JSONField
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('terra_geocrud', '0005_auto_20190724_1435'),
    ]

    operations = [
        migrations.AddField(
            model_name='crudview',
            name='settings',
            field=JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='crudview',
            name='ui_schema',
            field=JSONField(blank=True, default=dict),
        ),
    ]
