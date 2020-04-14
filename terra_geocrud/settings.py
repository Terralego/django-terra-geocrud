from copy import deepcopy

from PIL import Image
from django.conf import settings

Image.init()
_DEFAULT_TERRA_GEOCRUD = {
    # default extent to world
    'EXTENT': [-90.0, -180.0, 90.0, 180.0],
    'DATA_FILE_STORAGE_CLASS': 'django.core.files.storage.FileSystemStorage',
    # allowed image extensions are same as PIL support by default
    'IMAGE_EXTENSION_ALLOWED': [ext for ext in Image.EXTENSION],
    # give max_memory_size allowed by backend to api settings
    'FILE_UPLOAD_MAX_MEMORY_SIZE': settings.FILE_UPLOAD_MAX_MEMORY_SIZE,
    # Do not finish the url with a slash
    'MBGLRENDERER_URL': 'http://mbglrenderer',
    # We should automatically get the source of layers from a model
    'map': {
        "mapbox_access_token": None,
    },
    'STYLES': {
        'line': {
            'type': 'line',
            'paint': {
                'line-color': '#000',
                'line-width': 3
            }
        },
        'point': {
            'type': 'circle',
            'paint': {
                'circle-color': '#000',
                'circle-radius': 8
            }
        },
        'polygon': {
            'type': 'fill',
            'paint': {
                'fill-color': '#000'
            }
        },
    },
    'MAX_ZOOM': 15
}
_DEFAULT_TERRA_GEOCRUD.update(getattr(settings, 'TERRA_GEOCRUD', {}))
TERRA_GEOCRUD = deepcopy(_DEFAULT_TERRA_GEOCRUD)
