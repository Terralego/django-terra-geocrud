from django.http import HttpResponseNotFound
from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

app_name = 'terra_geocrud'

router = SimpleRouter()
router.register('groups', views.CrudGroupViewSet)
router.register('views', views.CrudViewViewSet)

urlpatterns = [
    path('api/crud/settings/', views.CrudSettingsApiView.as_view(), name="settings"),
    path('api/crud/', include(router.urls)),
    path('api/crud/template/<template_pk>/render/<pk>/',
         views.CrudRenderTemplateDetailView.as_view(), name='render-template'),
    path('api/crud/template/<template_pk>/render/{id}/',
         lambda request, **kwargs: HttpResponseNotFound(),
         name='render-template-pattern')
]
