from django.conf import settings

_DEFAULT_TERRA_GEOCRUD = {
    'EXTENT': ((-90.0, -180.0), (90.0, 180.0))
}
_DEFAULT_TERRA_GEOCRUD.update(getattr(settings, 'TERRA_GEOCRUD', {}))

TERRA_GEOCRUD_SETTINGS = _DEFAULT_TERRA_GEOCRUD
