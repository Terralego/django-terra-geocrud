import json
import os
from io import BytesIO
from zipfile import ZipFile

from django.core.files import File
from django.contrib.gis.geos import Point
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from geostore.models import Layer, Feature
from template_model.models import Template

from .. import models
from .settings import (DOCX_PLAN_DE_GESTION, FEATURE_PROPERTIES, LAYER_COMPOSANTES_SCHEMA,
                       SNAPSHOT_PLAN_DE_GESTION)


class CrudGroupViewSetTestCase(TestCase):
    def setUp(self):
        self.group = models.CrudGroupView.objects.create(name="group", order=0)
        self.api_client = APIClient()

    def test_list_endpoint(self):
        response = self.api_client.get(reverse('terra_geocrud:crudgroupview-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), models.CrudGroupView.objects.count())

        self.assertEqual(data[0]['id'], self.group.pk)

    def test_detail_endpoint(self):
        response = self.api_client.get(reverse('terra_geocrud:crudgroupview-detail', args=(self.group.pk, )))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data['id'], self.group.pk)


class CrudViewViewSetTestCase(TestCase):
    def setUp(self):
        self.group_1 = models.CrudGroupView.objects.create(name="group 1", order=0)
        self.group_2 = models.CrudGroupView.objects.create(name="group 2", order=1)
        self.view_1 = models.CrudView.objects.create(name="View 1", order=0, group=self.group_1,
                                                     layer=Layer.objects.create(name=1))
        self.view_2 = models.CrudView.objects.create(name="View 2", order=0, group=self.group_2,
                                                     layer=Layer.objects.create(name=2))
        self.view_3 = models.CrudView.objects.create(name="View 3", order=1, group=self.group_2,
                                                     layer=Layer.objects.create(name=3))
        self.api_client = APIClient()

    def test_list_endpoint(self):
        response = self.api_client.get(reverse('terra_geocrud:crudview-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), models.CrudView.objects.count())

        self.assertEqual(data[0]['id'], self.view_1.pk)

    def test_detail_endpoint(self):
        response = self.api_client.get(reverse('terra_geocrud:crudview-detail', args=(self.view_1.pk, )))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data['id'], self.view_1.pk)


class CrudSettingsViewTestCase(TestCase):
    def setUp(self):
        self.group_1 = models.CrudGroupView.objects.create(name="group 1", order=0)
        self.group_2 = models.CrudGroupView.objects.create(name="group 2", order=1)
        self.view_1 = models.CrudView.objects.create(name="View 1", order=0, group=self.group_1,
                                                     layer=Layer.objects.create(name=1))
        self.view_2 = models.CrudView.objects.create(name="View 2", order=0, group=self.group_2,
                                                     layer=Layer.objects.create(name=2))
        self.view_3 = models.CrudView.objects.create(name="View 3", order=1, group=self.group_2,
                                                     layer=Layer.objects.create(name=3))
        self.api_client = APIClient()
        self.response = self.api_client.get(reverse('terra_geocrud:settings'))

    def test_endpoint_access(self):
        self.assertEqual(self.response.status_code, status.HTTP_200_OK)

    def test_endpoint_menu(self):
        """
        Menu has 1 section per group, and 1 section for non grouped views
        """
        data = self.response.json()
        self.assertEqual(len(data['menu']), models.CrudGroupView.objects.count() + 1)

    def test_endpoint_config_without_settings(self):
        """
        Without extra settings, config section is empty
        """
        data = self.response.json()
        self.assertEqual(data['config'], {})

    @override_settings(TERRA_GEOCRUD={"terra_crud_settings_1": True})
    def test_endpoint_config_with_settings(self):
        """
        Extra TERRA_GEOCRUD settings are added to config section
        """
        self.response = self.api_client.get(reverse('terra_geocrud:settings'))
        data = self.response.json()
        self.assertEqual(data['config'], {"terra_crud_settings_1": True})


class CrudRenderTemplateDetailViewTestCase(TestCase):

    def setUp(self):
        self.layer = Layer.objects.create(
            name='composantes',
            schema=json.load(open(LAYER_COMPOSANTES_SCHEMA)),
            geom_type=1,
        )
        self.feature = Feature.objects.create(
            layer=self.layer,
            geom=Point(x=-0.246322800072846, y=44.5562461167907),
            properties=json.load(open(FEATURE_PROPERTIES)),
        )
        self.template = Template.objects.create(
            name='Template',
            template_file=File(open(DOCX_PLAN_DE_GESTION, 'rb')),
        )
        self.crud_view = models.CrudView.objects.create(name='view 1', order=0, layer=self.layer)
        self.crud_view.templates.add(self.template)
        self.api_client = APIClient()

    def test_works(self):
        response = self.api_client.get(
            reverse(
                'terra_geocrud:render-template',
                kwargs={'pk': self.feature.pk, 'template_pk': self.template.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response._headers['content-type'][-1],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        with open(SNAPSHOT_PLAN_DE_GESTION) as reader:
            content_xml = reader.read().encode('utf-8')
        buffer = BytesIO(response.content)
        with ZipFile(buffer) as archive:
            with archive.open(os.path.join('word', 'document.xml')) as reader:
                self.assertEqual(reader.read(), content_xml)

    def tearDown(self):
        os.remove(self.template.template_file.path)
