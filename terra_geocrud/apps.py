from django.apps import AppConfig
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from terra_accounts.permissions_mixins import PermissionRegistrationMixin


class TerraCrudConfig(PermissionRegistrationMixin, AppConfig):
    name = 'terra_geocrud'
    verbose_name = 'Geographic Editor Config'
    permissions = (
        ("can_manage_views", _("GEOCRUD: Can create / edit / delete views / groups and associated layers.")),
        ("can_view_feature", _("GEOCRUD: Can read feature detail.")),
        ("can_add_feature", _("GEOCRUD: Can create feature")),
        ("can_change_feature", _("GEOCRUD: Can change feature")),
        ("can_delete_feature", _("GEOCRUD: Can delete feature")),
    )

    def ready(self):
        super().ready()
        # in terra lego context, we assume to render module url
        terra_settings = getattr(settings, 'TERRA_APPLIANCE_SETTINGS', {})
        modules = terra_settings.get('modules', {})
        modules.update({
            'CRUD': {
                "settings": reverse_lazy('settings'),
            }
        })
        # then we add base layers in settings
        MapBaseLayer = self.apps.get_model('mapbox_baselayer.MapBaseLayer')
        base_layers = [
            {base_layer.name: {
                'id': base_layer.pk,
                'url': base_layer.url, }}
            for base_layer in MapBaseLayer.objects.all()
        ]
        terra_settings.update({'modules': modules,
                               'BASE_LAYERS': base_layers})
        setattr(settings, 'TERRA_APPLIANCE_SETTINGS', terra_settings)
