from collections import OrderedDict

from rest_framework.response import Response
from terra_utils.pagination import PagePagination


class GeoJsonPagination(PagePagination):
    def get_paginated_response(self, data):
        if self.request.kwargs.get('format', 'json') == 'geojson':
            return Response(OrderedDict([
                ('type', 'FeatureCollection'),
                ('count', self.page.paginator.count),
                ('next', self.get_next_link()),
                ('previous', self.get_previous_link()),
                ('features', data['features'])
            ]))
        return super().get_paginated_response(data)
