from django.apps import AppConfig
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from terra_accounts.permissions_mixins import PermissionRegistrationMixin


class TerraCrudConfig(PermissionRegistrationMixin, AppConfig):
    name = 'terra_geocrud'
    verbose_name = _('Geographic Editor (CRUD)')
    permissions = (
        ("can_manage_views", _("GEOCRUD: Can create / edit / delete views / groups and associated layers.")),
        ("can_view_feature", _("GEOCRUD: Can read feature detail.")),
        ("can_add_feature", _("GEOCRUD: Can create feature")),
        ("can_change_feature", _("GEOCRUD: Can change feature")),
        ("can_delete_feature", _("GEOCRUD: Can delete feature")),
    )

    def ready(self):
        super().ready()
        terra_settings = getattr(settings, 'TERRA_APPLIANCE_SETTINGS', {})
        modules = terra_settings.get('modules', {})
        # auto enable CRUD in terralego modules settings
        modules.update({
            'CRUD': {
                # in terra lego context, we assume to render module url
                "settings": reverse_lazy('settings'),
            }
        })
        terra_settings.update({'modules': modules})
        setattr(settings, 'TERRA_APPLIANCE_SETTINGS', terra_settings)
