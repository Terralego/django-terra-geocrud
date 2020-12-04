from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('groups', views.CrudGroupViewSet)
router.register('views', views.CrudViewViewSet)
router.register('attachment-categories', views.CrudAttachmentCategoryViewSet)
router.register(r'layers', views.CrudLayerViewSet, basename='layer')
router.register(r'layers/(?P<layer>[\d\w\-_]+)/features', views.CrudFeatureViewSet, basename='feature')
router.register(r'features/(?P<identifier>[0-9a-f-]+)/pictures',
                views.CrudFeaturePictureViewSet, basename='picture')
router.register(r'features/(?P<identifier>[0-9a-f-]+)/attachments',
                views.CrudFeatureAttachmentViewSet, basename='attachment')

urlpatterns = [
    path('', include(router.urls)),
    path('settings/', views.CrudSettingsApiView.as_view(), name="crud-settings"),
]
