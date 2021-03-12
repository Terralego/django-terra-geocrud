from django.contrib.gis.geos import Point

from geostore.models import LayerRelation


def get_length(feature):
    return feature.geom.length


def get_cities(feature):
    try:
        lr = LayerRelation.objects.get(name='cities')
        return list(feature.get_stored_relation_qs(lr.pk).exclude(properties__name=None).values_list('properties__name', flat=True))
    except LayerRelation.DoesNotExist:
        return []


def get_city(feature, id_point):
    start_point = Point(feature.geom[id_point]).ewkt
    lr = LayerRelation.objects.get(name='cities')
    return ', '.join(feature.get_stored_relation_qs(lr.pk).intersects(start_point).exclude(properties__name=None).values_list('properties__name', flat=True))


def get_first_city(feature):
    return get_city(feature, 0)


def get_last_city(feature):
    return get_city(feature, -1)
