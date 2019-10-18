from copy import deepcopy

from django.apps import AppConfig
from django.conf import settings
from django.urls import reverse_lazy
from . import settings as app_settings


class TerraCrudConfig(AppConfig):
    name = 'terra_geocrud'
    verbose_name = 'Geographic Editor Config'

    def ready(self):
        # in terra lego context, we assume to render module url
        terra_settings = getattr(settings, 'TERRA_APPLIANCE_SETTINGS', {})
        modules = terra_settings.get('modules', {})

        default_config = deepcopy(app_settings.TERRA_GEOCRUD)
        default_config.update(getattr(settings, 'TERRA_GEOCRUD', {}))

        modules.update({
            'CRUD': {
                "menu": reverse_lazy('terra_geocrud:settings'),
                "config": default_config
            }
        })
        terra_settings.update({'modules': modules})
        setattr(settings, 'TERRA_APPLIANCE_SETTINGS', terra_settings)
