from django.apps import AppConfig
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from sorl.thumbnail.conf import settings as thumbnail_settings
from terra_accounts.permissions_mixins import PermissionRegistrationMixin


class TerraCrudConfig(PermissionRegistrationMixin, AppConfig):
    name = 'terra_geocrud'
    verbose_name = _('Geographic Editor Config')
    permissions = (
        ("CRUD", "can_manage_views", _("CRUD: Can create / edit / delete views / groups and associated layers.")),
        ("CRUD", "can_view_feature", _("CRUD: Can read feature detail.")),
        ("CRUD", "can_add_feature", _("CRUD: Can create feature")),
        ("CRUD", "can_change_feature", _("CRUD: Can change feature")),
        ("CRUD", "can_delete_feature", _("CRUD: Can delete feature")),
    )

    def ready(self):
        if settings.AUTH_USER_MODEL == 'terra_accounts.TerraUser':
            # sync functionnal perms if using terra accounts auth user model
            super().ready()
            # in terra-admin context, we assume to render module url
            terra_settings = getattr(settings, 'TERRA_APPLIANCE_SETTINGS', {})
            modules = terra_settings.get('modules', {})
            modules.update({
                'CRUD': {
                    "settings": reverse_lazy('crud-settings'),
                }
            })
            terra_settings.update({'modules': modules})
            setattr(settings, 'TERRA_APPLIANCE_SETTINGS', terra_settings)
        # Thumbnails settings
        setattr(thumbnail_settings, 'THUMBNAIL_FORMAT', 'PNG')  # force PNG for thumbnail, to keep transparency
        setattr(thumbnail_settings, 'THUMBNAIL_UPSCALE', False)  # never upscale if image size < thumbnail size
        import terra_geocrud.signals  # NOQA
