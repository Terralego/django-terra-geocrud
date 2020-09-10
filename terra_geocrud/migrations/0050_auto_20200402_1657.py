try:
    from django.db.models import JSONField
except ImportError:  # TODO: Remove when dropping Django releases < 3.1
    from django.contrib.postgres.fields import JSONField
import django.contrib.postgres.indexes
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('terra_geocrud', '0049_auto_20200402_1350'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crudview',
            name='ui_schema',
            field=JSONField(blank=True, default=dict, editable=False, help_text='Custom ui:schema style for this entry.\n                                         https://react-jsonschema-form.readthedocs.io/en/latest/form-customization/'),
        ),
        migrations.AddIndex(
            model_name='crudviewproperty',
            index=django.contrib.postgres.indexes.GinIndex(fields=['json_schema'], name='json_schema_index', opclasses=['jsonb_path_ops']),
        ),
        migrations.AddIndex(
            model_name='crudviewproperty',
            index=django.contrib.postgres.indexes.GinIndex(fields=['ui_schema'], name='ui_schema_index', opclasses=['jsonb_path_ops']),
        ),
    ]
