import mimetypes
from copy import deepcopy
from pathlib import Path

import reversion
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.encoding import smart_text
from django.utils.translation import gettext as _
from django.views.generic.detail import DetailView
from geostore.models import Feature
from geostore.views import FeatureViewSet, LayerViewSet
from mapbox_baselayer.models import MapBaseLayer
from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from . import models, serializers, settings as app_settings


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
    queryset = models.CrudView.objects.all()
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


class CrudRenderTemplateDetailView(DetailView):
    model = Feature
    pk_template_field = 'pk'
    pk_template_kwargs = 'template_pk'

    def get_template_names(self):
        return self.template.template_file.name

    def get_template_object(self):
        return get_object_or_404(self.get_object().layer.crud_view.templates,
                                 **{self.pk_template_field:
                                    self.kwargs.get(self.pk_template_kwargs)})

    def render_to_response(self, context, **response_kwargs):
        self.template = self.get_template_object()
        self.content_type, _encoding = mimetypes.guess_type(self.get_template_names())
        response = super().render_to_response(context, **response_kwargs)
        path = Path(self.template.template_file.name)
        feature = self.get_object()
        feature_name = feature.layer.crud_view.get_feature_title(feature)
        new_name = f"{path.name.rstrip(path.suffix)}_{feature_name}{path.suffix}"
        response['Content-Disposition'] = f'attachment; filename={smart_text(new_name)}'
        return response


class CrudLayerViewSet(LayerViewSet):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES


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
        return serializers.CrudFeatureListSerializer


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
