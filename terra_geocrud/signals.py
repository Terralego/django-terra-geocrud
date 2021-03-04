import logging
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.module_loading import import_string

from geostore.models import Feature


logger = logging.getLogger(__name__)


def compute_properties(instance, prop):
    value = import_string(prop.function_path)(instance)
    old_value = instance.properties.get(prop.key)
    instance.properties[prop.key] = value
    try:
        instance.clean()
        instance.save(update_fields=['properties'])
    except ValidationError:
        logger.warning("The function to update property didn't give the good format, "
                       "fix your function or the schema")
        if old_value:
            instance.properties[prop.key] = old_value


def change_props(instance):
    crud_view = instance.layer.crud_view
    if crud_view:
        props = crud_view.properties.filter(editable=False).exclude(function_path='')
        for prop in props:
            compute_properties(instance, prop)


@receiver(post_save, sender=Feature)
def save_feature(sender, instance, **kwargs):
    if (kwargs.get('update_fields') is None or 'properties' not in kwargs.get('update_fields')) and hasattr(instance.layer, 'crud_view'):
        change_props(instance)
