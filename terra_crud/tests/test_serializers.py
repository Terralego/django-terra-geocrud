import os

from django.test import TestCase
from django.core.files import File
from template_model.models import Template

from ..serializers import EnrichedTemplateSerializer
from .settings import ODT_TEMPLATE


class EnrichedTemplateSerializerTestCase(TestCase):

    def setUp(self):
        self.template = Template.objects.create(
            name='Awsum template',
            template_file=File(open(ODT_TEMPLATE, 'rb')),
        )

    def test_works(self):
        serializer = EnrichedTemplateSerializer(instance=self.template)
        data = serializer.data
        self.assertEqual(data['id'], self.template.pk)
        self.assertTrue('/api/crud/template/%s/render/{pk}/' % self.template.pk in data['url'])
        self.assertEqual(data['name'], self.template.name)
        self.assertEqual(data['mime_type'], 'application/vnd.oasis.opendocument.text')

    def tearDown(self):
        os.remove(self.template.template_file.path)
