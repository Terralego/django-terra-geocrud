
def get_length(feature):
    return feature.geom.length


def get_cities(feature):
    return list(feature.relations.get('cities').values_list('properties__name', flat=True))
