import mimetypes
from copy import deepcopy

import reversion
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.encoding import smart_text
from django.utils.translation import gettext as _
from django.views.generic.detail import DetailView
from pathlib import Path
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from geostore.models import Feature
from geostore.views import FeatureViewSet
from . import models, serializers, settings as app_settings


def set_reversion_user(reversion, user):
    if not user.is_anonymous:
        reversion.set_user(user)


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
        ungrouped_views = models.CrudView.objects.filter(group__isnull=True)\
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
                "attachment_categories": reverse('terra_geocrud:attachmentcategory-list'),
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
        response['Content-Disposition'] = 'attachment; filename=%s' % smart_text(
            Path(self.template.template_file.name).name
        )
        return response


class CrudFeatureViewSet(ReversionMixin, FeatureViewSet):
    permission_classes = []

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related('layer__crud_view__templates')

    def get_serializer_class(self):
        if self.action in ('retrieve', 'update', 'partial_update', 'create'):
            return serializers.CrudFeatureDetailSerializer
        return serializers.CrudFeatureListSerializer

    @action(detail=True)
    def pictures(self, request, *args, **kwargs):
        pictures = self.get_object().pictures.all()
        ids_categories = pictures.values_list('category_id', flat=True)
        categories = models.AttachmentCategory.objects.filter(pk__in=ids_categories).distinct()
        context = self.get_serializer_context()
        context['pictures'] = pictures
        serializer = serializers.FeaturePictureCategorySerializer(categories,
                                                                  many=True,
                                                                  context=context)
        return Response(serializer.data)

    @action(detail=True)
    def attachments(self, request, *args, **kwargs):
        attachments = self.get_object().attachments.all()
        ids_categories = attachments.values_list('category_id', flat=True)
        categories = models.AttachmentCategory.objects.filter(pk__in=ids_categories).distinct()
        context = self.get_serializer_context()
        context['attachments'] = attachments
        serializer = serializers.FeatureAttachmentCategorySerializer(categories,
                                                                     many=True,
                                                                     context=context)
        return Response(serializer.data)


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
