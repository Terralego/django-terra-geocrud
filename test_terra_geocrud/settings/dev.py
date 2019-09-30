from . import *  # NOQA

TEST = False

ALLOWED_HOSTS = ['*']

INSTALLED_APPS += (
    'drf_yasg',
    'debug_toolbar',
)

MIDDLEWARE += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda x: True,
}
