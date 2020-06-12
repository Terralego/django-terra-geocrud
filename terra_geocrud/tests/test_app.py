from django.conf import settings
from django.test import TestCase, override_settings


import terra_geocrud
from terra_geocrud.apps import TerraCrudConfig


class AppSettingsTestCase(TestCase):
    def test_settings_accounts_enabled(self):
        with self.modify_settings(
                INSTALLED_APPS={"append": "terra_accounts"},
        ):
            with override_settings(AUTH_USER_MODEL='terra_accounts.TerraUser'):
                appconfig = TerraCrudConfig('terra_geocrud', terra_geocrud)
                appconfig.ready()
                self.assertDictEqual(settings.TERRA_APPLIANCE_SETTINGS,
                                     {'modules': {'CRUD': {'settings': '/api/crud/settings/'}}})
