from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/crud/', include('terra_geocrud.urls')),
    path('api/geostore/', include('geostore.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

try:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
except ImportError:
    pass
