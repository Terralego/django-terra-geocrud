try:
    from django.db.models import JSONField
except ImportError:  # TODO: Remove when dropping Django releases < 3.1
    from django.contrib.postgres.fields import JSONField
from django.db import migrations
import geostore.validators


class Migration(migrations.Migration):

    dependencies = [
        ('terra_geocrud', '0051_auto_20200420_0751'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crudviewproperty',
            name='json_schema',
            field=JSONField(default=dict, validators=[geostore.validators.validate_json_schema]),
        ),
    ]
