
def get_length(feature):
    return feature.geom.length


def get_cities(feature):
    cities = []
    for feature in feature.relations['cities']:
        cities.append(feature.destination.properties['name'])
    return cities
