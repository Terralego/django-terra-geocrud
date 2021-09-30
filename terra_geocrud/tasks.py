import logging
from celery import shared_task

from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string

from geostore.models import Feature, LayerRelation


logger = logging.getLogger(__name__)


class ConcurrentPropertyModificationError(Exception):
    """
    This exception is raised when an instance property field is being modified concurrently by two processes
    It means that a data race is happening. Maybe your property field should be marked as read-only ?
    """

    pass


def compute_properties(instance, prop):
    value = import_string(prop.function_path)(instance)
    old_value = instance.properties.get(prop.key)

    # Since this function is called in an async context, the 'properties' field might have been modified during our
    # computation. To avoid data loss we fetch the latest version of the dict and handle conflicting modifications.
    instance.refresh_from_db()

    value_from_db = instance.properties.get(prop.key)
    if value_from_db != old_value:
        raise ConcurrentPropertyModificationError(
            "A property has been modified while a computation was going on. Computed "
            "properties should be non-editable, check your configuration."
        )

    instance.properties[prop.key] = value
    try:
        instance.clean()
        # Avoiding signal post_save again
        Feature.objects.bulk_update([instance], ['properties'])
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
        feature_update_relations_and_properties.delay(feature.pk, kwargs)

    return True


def sync_properties_relations_destination(feature, update_relations=False):
    for relation_destination in feature.layer.relations_as_destination.all():
        for feature in relation_destination.origin.features.all():
            if update_relations:
                feature.sync_relations(relation_destination.pk)
            change_props(feature)  # TODO:  Compute link between relation and computed properties


@shared_task
def feature_update_relations_and_properties(feature_id, kwargs):
    """ Update all feature layer relations """
    try:
        feature = Feature.objects.get(pk=feature_id)
    except Feature.DoesNotExist:
        return False
    feature.sync_relations(None)

    sync_properties_relations_destination(feature, update_relations=True)

    change_props(feature)

    return True


@shared_task
def feature_update_destination_properties(feature_id, kwargs):
    try:
        feature = Feature.objects.get(pk=feature_id)
    except Feature.DoesNotExist:
        return False

    sync_properties_relations_destination(feature)


@shared_task
def layer_relations_set_destinations(relation_id):
    """ Update all feature layer as origin for a relation """
    try:
        relation = LayerRelation.objects.get(pk=relation_id)
    except LayerRelation.DoesNotExist:
        return False

    kwargs = {"relation_id": relation_id}
    for feature_id in relation.origin.features.values_list('pk', flat=True):
        feature_update_relations_and_properties.delay(feature_id, kwargs)

    return True
