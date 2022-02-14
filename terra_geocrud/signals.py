from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.db.models import signals

from geostore import settings as app_settings
from geostore.helpers import execute_async_func
from geostore.models import Feature, LayerRelation
from geostore.signals import save_feature, save_layer_relation
from terra_geocrud.properties.files import delete_feature_files
from terra_geocrud.tasks import (feature_update_relations_and_properties, layer_relations_set_destinations,
                                 feature_update_relations_origins, feature_update_destination_properties)


signals.post_save.disconnect(save_feature, sender=Feature)

signals.post_save.disconnect(save_layer_relation, sender=Feature)


def execute_async_save(update_fields, instance, kwargs):
    # update_fields=None (most of the time) .save()
    # update_fields=['geom', 'properties] => update everything
    if update_fields is None or 'geom' in update_fields:
        execute_async_func(feature_update_relations_and_properties, (instance.pk, kwargs))
    # update_fields=['properties'] => update only relations properties
    elif "properties" in update_fields:
        execute_async_func(feature_update_destination_properties, (instance.pk, kwargs))


@receiver(post_save, sender=Feature)
def save_feature(sender, instance, **kwargs):
    if app_settings.GEOSTORE_RELATION_CELERY_ASYNC:
        kwargs['relation_id'] = None
        kwargs.pop('signal')
        update_fields = kwargs.get('update_fields')
        kwargs['update_fields'] = list(update_fields) if update_fields else update_fields
        if hasattr(instance.layer, 'crud_view'):
            execute_async_save(update_fields, instance, kwargs)


@receiver(post_save, sender=LayerRelation)
def save_layer_relation(sender, instance, **kwargs):
    if app_settings.GEOSTORE_RELATION_CELERY_ASYNC:
        execute_async_func(layer_relations_set_destinations, (instance.pk, ))


@receiver(post_delete, sender=Feature, dispatch_uid='delete_files_feature')
def delete_files_feature(sender, instance, **kwargs):
    delete_feature_files(instance)


@receiver(post_delete, sender=Feature, dispatch_uid='delete_feature')
def delete_feature(sender, instance, **kwargs):
    # save base64 file content to storage
    if app_settings.GEOSTORE_RELATION_CELERY_ASYNC:
        kwargs['relation_id'] = None
        kwargs.pop('signal')
        features = []
        for relation_destination in instance.layer.relations_as_destination.all():
            features.extend(relation_destination.origin.features.values_list('id', flat=True))
        execute_async_func(feature_update_relations_origins, (features, kwargs))
