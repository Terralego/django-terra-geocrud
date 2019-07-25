from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from terracommon.terra.models import Layer

from .. import models


class CrudGroupViewSetTestCase(TestCase):
    def setUp(self):
        self.group = models.CrudGroupView.objects.create(name="group", order=0)
        self.api_client = APIClient()

    def test_list_endpoint(self):
        response = self.api_client.get(reverse('terra_crud:crudgroupview-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), models.CrudGroupView.objects.count())

        self.assertEqual(data[0]['id'], self.group.pk)

    def test_detail_endpoint(self):
        response = self.api_client.get(reverse('terra_crud:crudgroupview-detail', args=(self.group.pk, )))
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
        response = self.api_client.get(reverse('terra_crud:crudview-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), models.CrudView.objects.count())

        self.assertEqual(data[0]['id'], self.view_1.pk)

    def test_detail_endpoint(self):
        response = self.api_client.get(reverse('terra_crud:crudview-detail', args=(self.view_1.pk, )))
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
        self.response = self.api_client.get(reverse('terra_crud:settings'))

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

    @override_settings(TERRA_CRUD={"terra_crud_settings_1": True})
    def test_endpoint_config_with_settings(self):
        """
        Extra TERRA_CRUD settings are added to config section
        """
        self.response = self.api_client.get(reverse('terra_crud:settings'))
        data = self.response.json()
        self.assertEqual(data['config'], {"terra_crud_settings_1": True})
