from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

app_name = 'terra_geocrud'

router = SimpleRouter()
router.register('groups', views.CrudGroupViewSet)
router.register('views', views.CrudViewViewSet)
router.register(r'layer/(?P<layer>[\d\w\-_]+)/features', views.CrudFeatureViewsSet, base_name='feature')

urlpatterns = [
    path('api/crud/', include(router.urls)),
    path('api/crud/settings/', views.CrudSettingsApiView.as_view(), name="settings"),
    # template rendering
    path('api/crud/template/<template_pk>/render/<pk>/',
         views.CrudRenderTemplateDetailView.as_view(), name='render-template'),
    path('api/crud/features/<int:pk>/<slug:key>/', views.CrudFeatureFileAPIView.as_view(), name='render-file')
]
