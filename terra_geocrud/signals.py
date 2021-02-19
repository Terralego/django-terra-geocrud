from importlib import import_module
from django.db.models.signals import post_save
from django.dispatch import receiver

from geostore.models import Feature


json_schema_cast = {
    "integer": int,
    "string": str
}


@receiver(post_save, sender=Feature)
def save_feature(sender, instance, **kwargs):
    if kwargs.get('update_fields') is None or 'properties' not in kwargs.get('update_fields'):
        crud_view = instance.layer.crud_view
        if crud_view:
            props = crud_view.properties.filter(editable=False).exclude(function_path='')
            for prop in props:
                val = prop.function_path.split('.')
                function = val[-1]
                module_path = '.'.join(val[:-1])
                module = import_module(module_path)
                prop_cast = prop.json_schema.get('type')
                cast = json_schema_cast.get(prop_cast)
                value = getattr(module, function)(instance)
                instance.properties[prop.key] = cast(value)
        instance.save(update_fields=['properties'])
