from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('geostore.urls')),
    path('', include('terra_geocrud.urls', namespace='terra_geocrud')),
]

try:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
except ImportError:
    pass
