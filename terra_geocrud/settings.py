from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db.models import CharField

DATA_FILE_STORAGE_CLASS = 'django.core.files.storage.FileSystemStorage'
MBGLRENDERER_URL = 'http://mbglrenderer'
MBGLRENDERER_MAX_ZOOM = 22
MAPBOX_ACCESS_TOKEN = None

DEFAULT_MAP_CENTER_LAT = 0.0
DEFAULT_MAP_CENTER_LNG = 0.0
DEFAULT_MAP_CENTER_ZOOM = 2
DEFAULT_MAP_MAX_ZOOM = 18
DEFAULT_MAP_MIN_ZOOM = 3

MAP_EXTENT_SW_LAT = -90.0
MAP_EXTENT_SW_LNG = -180.0
MAP_EXTENT_NE_LAT = 90.0
MAP_EXTENT_NE_LNG = 180.0

DEFAULT_STYLE_LINE = {
    "type": "line",
    "paint": {
        "line-color": "#000",
        "line-width": 3
    }
}

DEFAULT_STYLE_POINT = {
    "type": "circle",
    "paint": {
        "circle-color": "#000",
        "circle-radius": 8
    }
}

DEFAULT_STYLE_POLYGON = {
    "type": "fill",
    "paint": {
        "fill-color": "#000"
    }
}

if 'siteprefs' in settings.INSTALLED_APPS:
    # Respect those users who doesn't have siteprefs installed.

    from siteprefs.toolbox import preferences

    with preferences() as prefs:
        prefs(  # Now we register our settings to make them available as siteprefs.
            # First we define a group of related settings, and mark them non-static (editable).
            prefs.group(
                'Map General settings',
                (prefs.one(
                    MAPBOX_ACCESS_TOKEN,
                    field=CharField(max_length=1024),
                    verbose_name='MapBox token', static=False,
                    help_text='To access to MapBox services.', ),
                 prefs.one(
                     DEFAULT_MAP_CENTER_LAT,
                     verbose_name='Default map center latitude', static=False,
                     help_text='In decimal WGS84', ),
                 prefs.one(
                     DEFAULT_MAP_CENTER_LNG,
                     verbose_name='Default map center longitude', static=False,
                     help_text='In decimal WGS84', ),
                 prefs.one(
                     DEFAULT_MAP_CENTER_ZOOM,
                     verbose_name='Default map zoom', static=False),
                 prefs.one(
                     DEFAULT_MAP_MAX_ZOOM,
                     verbose_name='Map max zoom', static=False),
                 prefs.one(
                     DEFAULT_MAP_MIN_ZOOM,
                     verbose_name='Map min zoom', static=False),
                 prefs.one(
                     DEFAULT_STYLE_LINE,
                     field=JSONField(default=dict),
                     verbose_name='Default style for lines', static=False),
                 prefs.one(
                     DEFAULT_STYLE_POINT,
                     field=JSONField(default=dict),
                     verbose_name='Default style for points', static=False),
                 prefs.one(
                     DEFAULT_STYLE_POLYGON,
                     field=JSONField(default=dict),
                     verbose_name='Default style for polygons', static=False),
                 prefs.one(
                     MAP_EXTENT_SW_LAT,
                     verbose_name='Extent : SW latitude',
                     help_text="in decimal WGS84",
                     static=False),
                 prefs.one(
                     MAP_EXTENT_SW_LNG,
                     verbose_name='Extent : SW longitude',
                     help_text="in decimal WGS84",
                     static=False),
                 prefs.one(
                     MAP_EXTENT_NE_LAT,
                     verbose_name='Extent : NE latitude',
                     help_text="in decimal WGS84",
                     static=False),
                 prefs.one(
                     MAP_EXTENT_NE_LNG,
                     verbose_name='Extent : NE longitude',
                     help_text="in decimal WGS84",
                     static=False),
                 ),
                static=False),
            prefs.one(
                DATA_FILE_STORAGE_CLASS,
                field=CharField(max_length=1024),
                verbose_name='Features data file storage class',
                help_text="WARNING ! Be careful with this settings. Make sure it exists",
                static=False),
            prefs.one(
                MBGLRENDERER_URL,
                field=CharField(max_length=2048),
                verbose_name='Customize mbglrenderer url', static=False,
                help_text="WARNING ! Be careful with this settings. Make sure it exists", ),
            prefs.one(
                MBGLRENDERER_MAX_ZOOM,
                verbose_name='Max zoom for map captures', static=False,
                help_text="Zoom is computed by extent, but required a max value for points", ),
        )
