try:
    from django.db.models import JSONField
except ImportError:  # TODO: Remove when dropping Django releases < 3.1
    from django.contrib.postgres.fields import JSONField
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('terra_geocrud', '0011_auto_20190902_0830'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crudview',
            name='ui_schema',
            field=JSONField(blank=True, default=dict, help_text='https://react-jsonschema-form.readthedocs.io/en/latest/form-customization/'),
        ),
    ]
