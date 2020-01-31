import factory
from template_model.models import Template

from geostore import GeometryTypes
from geostore.tests.factories import LayerFactory
from terra_geocrud.models import CrudView, FeaturePicture, AttachmentCategory, FeatureAttachment
from terra_geocrud.tests.settings import DOCX_TEMPLATE


class TemplateDocxFactory(factory.DjangoModelFactory):
    name = "Complex template"
    template_file = factory.django.FileField(from_path=DOCX_TEMPLATE)

    class Meta:
        model = Template


class CrudViewFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: "Name %03d" % n)
    order = 0
    layer = factory.SubFactory(
        LayerFactory,
        geom_type=GeometryTypes.Point,
        schema={
            "type": "object",
            "required": ["name", ],
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


class AttachmentCategoryFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: "Name %03d" % n)
    pictogram = factory.django.ImageField(color='green')

    class Meta:
        model = AttachmentCategory


class FeaturePictureFactory(factory.DjangoModelFactory):
    image = factory.django.ImageField(color='blue')
    category = factory.SubFactory(AttachmentCategoryFactory)

    class Meta:
        model = FeaturePicture


class FeatureAttachmentFactory(factory.DjangoModelFactory):
    file = factory.django.FileField(name='toto.pdf')
    category = factory.SubFactory(AttachmentCategoryFactory)

    class Meta:
        model = FeatureAttachment
