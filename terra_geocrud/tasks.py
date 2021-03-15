import logging
from celery import shared_task

from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string

from geostore.models import Feature, LayerRelation


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


def change_props(feature):
    crud_view = feature.layer.crud_view
    if crud_view:
        props = crud_view.properties.filter(editable=False).exclude(function_path='')
        for prop in props:
            compute_properties(feature, prop)


@shared_task
def feature_update_relations_origins(features_id, kwargs):
    features = Feature.objects.filter(pk__in=features_id)
    for feature in features:
        feature_update_relations_destinations.delay(feature.pk, kwargs)

    return True


def sync_relations_destination(feature, kwargs):
    for relation_destination in feature.layer.relations_as_destination.all():
        for feature in relation_destination.origin.features.all():
            feature.sync_relations(kwargs['relation_id'])
    return feature


@shared_task
def feature_update_relations_destinations(feature_id, kwargs):
    """ Update all feature layer relations """
    try:
        feature = Feature.objects.get(pk=feature_id)
    except Feature.DoesNotExist:
        return False

    feature.sync_relations(kwargs['relation_id'])

    feature = sync_relations_destination(feature, kwargs)

    if (kwargs.get('update_fields') is None or 'properties' not in kwargs.get('update_fields')) and hasattr(
            feature.layer, 'crud_view'):
        change_props(feature)

    return True


@shared_task
def layer_relations_set_destinations(relation_id):
    """ Update all feature layer as origin for a relation """
    try:
        relation = LayerRelation.objects.get(pk=relation_id)
    except LayerRelation.DoesNotExist:
        return False

    kwargs = {"relation_id": relation_id}
    for feature_id in relation.origin.features.values_list('pk', flat=True):
        feature_update_relations_destinations.delay(feature_id, kwargs)

    return True
