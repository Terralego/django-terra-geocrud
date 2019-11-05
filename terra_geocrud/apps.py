from django.apps import AppConfig
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from terra_accounts.permissions_mixins import PermissionRegistrationMixin


class TerraCrudConfig(PermissionRegistrationMixin, AppConfig):
    name = 'terra_geocrud'
    verbose_name = 'Geographic Editor Config'
    permissions = (
        ("geocrud_can_manage_views", _("GEOCRUD: Can create / edit / delete views / groups and associated layers.")),
        ("geocrud_can_view_feature", _("GEOCRUD: Can read feature detail.")),
        ("geocrud_can_add_feature", _("GEOCRUD: Can create feature")),
        ("geocrud_can_change_feature", _("GEOCRUD: Can change feature")),
        ("geocrud_can_delete_feature", _("GEOCRUD: Can delete feature")),
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
        terra_settings.update({'modules': modules})
        setattr(settings, 'TERRA_APPLIANCE_SETTINGS', terra_settings)
