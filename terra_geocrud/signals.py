from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from django.db.models import signals

from geostore import settings as app_settings
from geostore.helpers import execute_async_func
from geostore.models import Feature
from geostore.signals import save_feature
from terra_geocrud.tasks import feature_update_relations_destinations


signals.post_save.disconnect(save_feature, sender=Feature)


@receiver(post_save, sender=Feature)
def save_feature(sender, instance, **kwargs):
    if app_settings.GEOSTORE_RELATION_CELERY_ASYNC:
        kwargs['relation_id'] = None
        kwargs.pop('signal')
        update_fields = kwargs.get('update_fields')
        kwargs['update_fields'] = list(update_fields) if update_fields else update_fields
        execute_async_func(feature_update_relations_destinations, (instance.pk, kwargs))
