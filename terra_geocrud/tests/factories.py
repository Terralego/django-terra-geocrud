import factory

from geostore import GeometryTypes
from geostore.tests.factories import LayerFactory
from terra_geocrud.models import CrudView


class CrudViewFactory(factory.DjangoModelFactory):
    name = factory.faker.Faker('name')
    order = 0
    layer = factory.SubFactory(
        LayerFactory,
        geom_type=GeometryTypes.Point,
        schema={
            "type": "object",
            "properties": {
                "name": {
                    'type': "string",
                    "title": "Name"
                },
                "age": {
                    'type': "integer",
                    "title": "Age",
                },
                "country": {
                    'type': "string",
                    "title": "Country"
                },
            }
        }
    )

    class Meta:
        model = CrudView
