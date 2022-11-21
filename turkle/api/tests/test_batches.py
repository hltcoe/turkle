from django.urls import reverse
from rest_framework import status

from turkle.models import Batch, Project

from . import TurkleAPITestCase


class ProjectsTests(TurkleAPITestCase):
    def setUp(self):
        super().setUp()
        self.project, created = Project.objects.get_or_create(
            name='Test Project',
            html_template='<html><label>%{object}</label><input name="ans" type="text"><html>'
        )

    def test_create(self):
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'project': self.project.id,
            'csv_text': 'object\nbirds\ndogs',
            'filename': 'data.csv'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Batch.objects.count(), 1)
        batch = Batch.objects.get(id=1)
        self.assertEqual(batch.name, 'Batch 1')
        self.assertTrue(batch.active)
        self.assertTrue(batch.published)
        self.assertEqual(batch.total_tasks(), 2)

    def test_create_with_empty_csv(self):
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'project': self.project.id,
            'csv_text': '',
            'filename': 'data.csv'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, b'{"csv_text":["This field may not be blank."]}')

    def test_create_with_missing_csv(self):
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'project': self.project.id,
            'filename': 'data.csv'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, b'{"csv_text":["This field is required."]}')

    def test_create_with_incompatible_login_required_and_assignments_per_task(self):
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'project': self.project.id,
            'csv_text': 'object\nbirds\ndogs',
            'filename': 'data.csv',
            'login_required': False,
            'assignments_per_task': 2
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(b'When login is not required to access the Batch' in response.content)

    def test_create_with_incompatible_assignments_per_task_but_login_not_set(self):
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'project': self.project.id,
            'csv_text': 'object\nbirds\ndogs',
            'filename': 'data.csv',
            'assignments_per_task': 2
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
