import mimetypes

from django.conf import settings
from django.utils.encoding import smart_text
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from django.views.generic.detail import DetailView
from rest_framework import viewsets, response
from rest_framework.views import APIView
from geostore.models import Feature

from . import models, serializers


class CrudGroupViewSet(viewsets.ModelViewSet):
    queryset = models.CrudGroupView.objects.prefetch_related('crud_views__layer')
    serializer_class = serializers.CrudGroupSerializer


class CrudViewViewSet(viewsets.ModelViewSet):
    queryset = models.CrudView.objects.all()
    serializer_class = serializers.CrudViewSerializer


class CrudSettingsApiView(APIView):
    def get_config_section(self):
        config = {}

        terra_crud_settings = getattr(settings, 'TERRA_GEOCRUD', {})
        if terra_crud_settings:
            config.update(terra_crud_settings)

        return config

    def get_menu_section(self):
        groups = models.CrudGroupView.objects.prefetch_related('crud_views__layer')
        group_serializer = CrudGroupViewSet.serializer_class(groups, many=True)
        data = group_serializer.data

        # add non grouped views
        ungrouped_views = models.CrudView.objects.filter(group__isnull=True)
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
        return response.Response(data)


class CrudRenderTemplateDetailView(DetailView):
    model = Feature
    pk_template_field = 'pk'
    pk_template_kwargs = 'template_pk'

    def get_template_names(self):
        return self.template.template_file.name

    def render_to_response(self, context, **response_kwargs):
        self.template = get_object_or_404(
            self.get_object().layer.crud_view.templates,
            **{
                self.pk_template_field: self.kwargs.get(self.pk_template_kwargs)
            },
        )
        self.content_type, _encoding = mimetypes.guess_type(
            self.template.template_file.name)
        response = super().render_to_response(context, **response_kwargs)
        response['Content-Disposition'] = 'attachment; filename=%s' % smart_text(self.template.template_file.name)
        return response
