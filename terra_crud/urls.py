from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register('groups', views.CrudGroupViewSet)
router.register('views', views.CrudViewViewSet)

urls_patterns = [
    path('api/crud/', include(router.urls)),
]
