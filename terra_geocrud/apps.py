from django.apps import AppConfig
from django.conf import settings
from django.urls import reverse_lazy


class TerraCrudConfig(AppConfig):
    name = 'terra_geocrud'
    verbose_name = 'Geographic Editor Config'

    def ready(self):
        # in terra lego context, we assume to render module url
        terra_settings = getattr(settings, 'TERRA_APPLIANCE_SETTINGS', {})
        modules = terra_settings.get('modules', {})
        modules.update({
            'CRUD': {
                "settings": reverse_lazy('terra_geocrud:settings'),
            }
        })
        terra_settings.update({'modules': modules})
        setattr(settings, 'TERRA_APPLIANCE_SETTINGS', terra_settings)
