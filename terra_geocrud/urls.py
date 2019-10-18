from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

app_name = 'terra_geocrud'

router = SimpleRouter()
router.register('groups', views.CrudGroupViewSet)
router.register('views', views.CrudViewViewSet)
router.register('attachment-categories', views.CrudAttachmentCategoryViewSet)
router.register('attachments', views.CrudFeatureAttachmentViewSet, base_name='attachment')
router.register('pictures', views.CrudFeaturePictureViewSet, base_name='picture')
router.register(r'layers/(?P<layer>[\d\w\-_]+)/features', views.CrudFeatureViewSet, base_name='feature')

urlpatterns = [
    path('', include(router.urls)),
    path('settings/', views.CrudSettingsApiView.as_view(), name="settings"),
    # template rendering
    path('template/<template_pk>/render/<pk>/',
         views.CrudRenderTemplateDetailView.as_view(), name='render-template'),
]
