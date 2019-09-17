import base64
import mimetypes

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.encoding import smart_text
from django.utils.text import slugify


class CachedTemplateResponseMixin:
    uses_cache = getattr(settings, 'RENDER_TEMPLATE_USES_CACHE', False)

    def load_attributs(self):
        self.object = self.get_object()
        self.template = get_object_or_404(
            self.object.layer.crud_view.templates,
            **{
                self.pk_template_field: self.kwargs.get(self.pk_template_kwargs)
            },
        )
        self.content_type, _encoding = mimetypes.guess_type(self.template.template_file.name)

        if self.uses_cache:
            delta = self.object.updated_at - self.template.updated
            self.cached_filled_template_id = '{0}_{1}_{2}'.format(
                slugify(self.template.name),
                self.object.identifier,
                abs(int(delta.total_seconds()))
            )
            self.cached_filled_template = cache.get(self.cached_filled_template_id)

    def get_template_names(self):
        return self.template.template_file.name

    def get(self, request, *args, **kwargs):
        self.load_attributs()
        if self.uses_cache and self.cached_filled_template:
            content = base64.b64decode(self.cached_filled_template)
            response = HttpResponse(content=content, content_type=self.content_type)
        else:
            context = self.get_context_data(object=self.object)
            response = self.render_to_response(context)
            if self.uses_cache:
                cache.set(
                    self.cached_filled_template_id,
                    base64.b64encode(response.rendered_content).decode())
        response['Content-Disposition'] = 'attachment; filename={}'.format(
            smart_text(self.template.template_file.name))
        return response
