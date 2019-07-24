from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

app_name = 'terra_crud'

router = SimpleRouter()
router.register('groups', views.CrudGroupViewSet)
router.register('views', views.CrudViewViewSet)

urlpatterns = [
    path('api/crud/', include(router.urls)),
]
