import mimetypes
import base64

from django.conf import settings
from django.core.files.base import ContentFile
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.utils.encoding import smart_text
from django.utils.translation import gettext as _
from django.views.generic.detail import DetailView
from rest_framework import viewsets
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from geostore.models import Feature
from geostore.views import FeatureViewSet
from . import models, serializers, settings as app_settings


class CrudGroupViewSet(viewsets.ModelViewSet):
    queryset = models.CrudGroupView.objects.prefetch_related('crud_views__layer')
    serializer_class = serializers.CrudGroupSerializer


class CrudViewViewSet(viewsets.ModelViewSet):
    queryset = models.CrudView.objects.all()
    serializer_class = serializers.CrudViewSerializer


class CrudSettingsApiView(APIView):
    def get_config_section(self):
        default_config = app_settings.TERRA_GEOCRUD.copy()
        default_config.update(getattr(settings, 'TERRA_GEOCRUD', {}))
        return default_config

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
        data = {
            "menu": self.get_menu_section(),
            "config": self.get_config_section(),
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
        response['Content-Disposition'] = 'attachment; filename=%s' % smart_text(self.template.template_file.name)
        return response


class CrudFeatureFileAPIView(RetrieveAPIView):
    """ View that serve data url stored property as a file download """
    queryset = Feature.objects.select_related('layer__crud_view')

    def get(self, request, pk, key, **kwargs):
        """ Generate and download file from data-url encoded data """
        feature = self.get_object()
        file_data = feature.properties.get(key)

        if not file_data or feature.layer.schema.get('properties', {}).get(key, {}).get('format') != 'data-url':
            # if key doesn't exists, is empty or is not data-url
            return HttpResponseNotFound()

        else:
            meta, content = file_data.split(';base64,')
            metas = meta.split(';')
            response = HttpResponse(ContentFile(base64.b64decode(content)),
                                    content_type=metas[0])
            if len(metas) > 1:
                file_name = metas[1].split('=')[1]
                response['Content-Disposition'] = 'attachment; filename=%s' % smart_text(file_name)
        return response


class CrudFeatureViewsSet(FeatureViewSet):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related('layer')

    def get_serializer_class(self):
        if self.action in ('retrieve', 'update', 'partial_update', 'create'):
            return serializers.CrudFeatureDetailSerializer
        return serializers.CrudFeatureListSerializer
