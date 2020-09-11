try:
    from django.db.models import JSONField
except ImportError:  # TODO: Remove when dropping Django releases < 3.1
    from django.contrib.postgres.fields import JSONField
from django.db import migrations
import terra_geocrud.validators


class Migration(migrations.Migration):

    dependencies = [
        ('terra_geocrud', '0052_auto_20200420_0812'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crudviewproperty',
            name='json_schema',
            field=JSONField(default=dict, validators=[terra_geocrud.validators.validate_schema_property]),
        ),
    ]
