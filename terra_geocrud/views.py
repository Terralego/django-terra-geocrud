import mimetypes
from copy import deepcopy
from pathlib import Path

import reversion
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils import formats, timezone
from django.utils.module_loading import import_string
from django.utils.translation import gettext as _
from geostore import settings as geostore_settings
from geostore.models import Feature, Layer
from geostore.serializers import FeatureSerializer
from geostore.views import FeatureViewSet
from mapbox_baselayer.models import MapBaseLayer
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from . import models, serializers, settings as app_settings

# use BaseViewsSet as defined in geostore settings. using django-geostore-routing change this value
LayerViewSet = import_string(geostore_settings.GEOSTORE_LAYER_VIEWSSET)


def set_reversion_user(_reversion, user):
    if not user.is_anonymous:
        _reversion.set_user(user)


class ReversionMixin:
    def perform_create(self, serializer):
        with transaction.atomic(), reversion.create_revision():
            response = super().perform_create(serializer)
            set_reversion_user(reversion, self.request.user)
            return response

    def perform_update(self, serializer):
        with transaction.atomic(), reversion.create_revision():
            response = super().perform_update(serializer)
            set_reversion_user(reversion, self.request.user)
            return response


class CrudGroupViewSet(ReversionMixin, viewsets.ModelViewSet):
    queryset = models.CrudGroupView.objects.prefetch_related('crud_views__layer')
    serializer_class = serializers.CrudGroupSerializer


class CrudViewViewSet(ReversionMixin, viewsets.ModelViewSet):
    queryset = models.CrudView.objects.prefetch_related('routing_settings')
    serializer_class = serializers.CrudViewSerializer


class CrudSettingsApiView(APIView):
    def get_menu_section(self):
        groups = models.CrudGroupView.objects.prefetch_related('crud_views__layer',
                                                               'crud_views__feature_display_groups')
        group_serializer = CrudGroupViewSet.serializer_class(groups, many=True)
        data = group_serializer.data

        # add non grouped views
        ungrouped_views = models.CrudView.objects.filter(group__isnull=True,
                                                         visible=True)\
            .select_related('layer')\
            .prefetch_related('feature_display_groups')
        views_serializer = CrudViewViewSet.serializer_class(ungrouped_views, many=True)
        data.append({
            "id": None,
            "name": _("Unclassified"),
            "order": None,
            "pictogram": None,
            "crud_views": views_serializer.data
        })
        return data

    def get(self, request, *args, **kwargs):
        default_config = deepcopy(app_settings.TERRA_GEOCRUD)
        default_config.update(getattr(settings, 'TERRA_GEOCRUD', {}))

        data = {
            "menu": self.get_menu_section(),
            "config": {
                "default": default_config,
                'BASE_LAYERS': [
                    {base_layer.name: {
                        'id': base_layer.pk,
                        'url': base_layer.url, }}
                    for base_layer in MapBaseLayer.objects.all()
                ],
                "attachment_categories": reverse('attachmentcategory-list'),
            }
        }
        return Response(data)


class CrudLayerViewSet(LayerViewSet):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES

    def get_queryset(self):
        if self.action == 'route':
            return Layer.objects.filter(routable=True)
        return Layer.objects.exclude(crud_view__isnull=True)


class CrudFeatureViewSet(ReversionMixin, FeatureViewSet):
    serializer_class_extra_geom = serializers.CrudFeatureExtraGeomSerializer
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related('layer__crud_view__templates',
                                   'layer__extra_geometries',
                                   'extra_geometries')

    def get_serializer_class(self):
        if self.action in ('retrieve', 'update', 'partial_update', 'create'):
            return serializers.CrudFeatureDetailSerializer
        if self.action == 'relation':
            return self.transform_serializer_geojson(FeatureSerializer)
        return serializers.CrudFeatureListSerializer

    @action(detail=True, methods=['get'], permission_classes=[],
            url_path=r'generate-template/(?P<id_template>\d+)', url_name='generate-template')
    def generate_template(self, request, *args, **kwargs):
        """ Custom action to serve generated document from templates """
        feature = self.get_object()
        template = get_object_or_404(feature.layer.crud_view.templates.all(),
                                     pk=self.kwargs.get('id_template'))
        content_type, _encoding = mimetypes.guess_type(template.template_file.name)
        path = Path(template.template_file.name)
        original_suffix = path.suffix
        for suffix in path.suffixes:
            if 'pdf' in suffix:
                content_type = "application/pdf"
                original_suffix = ".pdf"
        feature_name = feature.layer.crud_view.get_feature_title(feature)
        date_formatted = formats.date_format(timezone.localtime(), "SHORT_DATETIME_FORMAT")
        new_name = f"{template.name}_{feature_name}_{date_formatted}{original_suffix}"

        response = TemplateResponse(
            request=self.request,
            template=template.template_file.name,
            context={'object': feature},
            **{'content_type': content_type}
        )
        response['Content-Disposition'] = f'attachment; filename="{new_name}"'
        return response


class CrudAttachmentCategoryViewSet(ReversionMixin, viewsets.ModelViewSet):
    queryset = models.AttachmentCategory.objects.all()
    serializer_class = serializers.AttachmentCategorySerializer


class BehindFeatureMixin:
    """ Helper for Feature's related viewsets """
    filter_backends = (filters.OrderingFilter, filters.SearchFilter)
    search_fields = ('legend', 'image')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature = None

    def get_feature(self):
        uuid = self.kwargs.get('identifier')
        if not self.feature and uuid:
            self.feature = get_object_or_404(Feature, identifier=uuid) if uuid else self.feature
        return self.feature

    def perform_create(self, serializer):
        serializer.save(feature=self.get_feature())


class CrudFeaturePictureViewSet(ReversionMixin, BehindFeatureMixin, viewsets.ModelViewSet):
    serializer_class = serializers.FeaturePictureSerializer

    def get_queryset(self):
        return self.get_feature().pictures.all()


class CrudFeatureAttachmentViewSet(ReversionMixin, BehindFeatureMixin, viewsets.ModelViewSet):
    serializer_class = serializers.FeatureAttachmentSerializer

    def get_queryset(self):
        return self.get_feature().attachments.all()
