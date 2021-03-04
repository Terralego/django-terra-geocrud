
def get_length(feature):
    return feature.geom.length


def get_cities(feature):
    return list(feature.get_stored_relation_qs(1).values_list('properties__name', flat=True))
