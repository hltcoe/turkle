from django.contrib.auth.models import Group
from django.urls import reverse
import guardian.shortcuts
from rest_framework import status

from turkle.models import Batch, Project, User

from . import TurkleAPITestCase


class BatchTests(TurkleAPITestCase):
    def setUp(self):
        super().setUp()
        self.project, created = Project.objects.get_or_create(
            name='Test Project',
            html_template='<html><label>%{label}</label><input name="ans" type="text"><html>'
        )
        self.project.fieldnames = dict((fn, True) for fn in ['label'])
        self.project.save()

    def test_create(self):
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'project': self.project.id,
            'csv_text': 'label\nbirds\ndogs',
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

    def test_create_with_missing_csv_field(self):
        self.project.fieldnames = dict((fn, True) for fn in ['label', 'text'])
        self.project.save()
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'project': self.project.id,
            'csv_text': 'label\nbirds\ndogs',
            'filename': 'data.csv'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'The missing fields are: text', response.content)

    def test_create_with_missing_project(self):
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'csv_text': 'label\nbirds\ndogs',
            'filename': 'data.csv'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'This field is required', response.content)

    def test_create_with_non_existent_project(self):
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'project': 99,
            'csv_text': 'label\nbirds\ndogs',
            'filename': 'data.csv'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Invalid pk', response.content)

    def test_create_with_incompatible_login_required_and_assignments_per_task(self):
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'project': self.project.id,
            'csv_text': 'label\nbirds\ndogs',
            'filename': 'data.csv',
            'login_required': False,
            'assignments_per_task': 2
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'When login is not required to access the Batch', response.content)

    def test_create_with_incompatible_assignments_per_task_but_login_not_set(self):
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'project': self.project.id,
            'csv_text': 'label\nbirds\ndogs',
            'filename': 'data.csv',
            'assignments_per_task': 2
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_inherit_login_required(self):
        project = Project.objects.create(login_required=False)
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'project': project.id,
            'csv_text': 'label\nbirds\ndogs',
            'filename': 'data.csv',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        batch = Batch.objects.get(id=1)
        self.assertEqual(project.login_required, batch.login_required)

    def test_create_inherit_permissions(self):
        project = Project.objects.create(login_required=True, custom_permissions=True)
        user1 = User.objects.create_user('testuser1', 'password')
        group1 = Group.objects.create(name='test')
        guardian.shortcuts.assign_perm('can_work_on', user1, project)
        guardian.shortcuts.assign_perm('can_work_on', group1, project)
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'project': project.id,
            'csv_text': 'label\nbirds\ndogs',
            'filename': 'data.csv',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        batch = Batch.objects.get(id=1)
        self.assertTrue(batch.custom_permissions)
        self.assertEqual([user.id for user in batch.get_user_custom_permissions()], [user1.id])
        self.assertEqual([group.id for group in batch.get_group_custom_permissions()], [group1.id])

    def test_setting_permissions(self):
        project = Project.objects.create(login_required=True, custom_permissions=True)
        batch = Batch.objects.create(project=project)
        url = reverse('batch-permissions-list', args=[batch.id])
        data = {
            'users': [1],
            'groups': [1],
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        batch = Batch.objects.get(id=batch.id)
        self.assertTrue(batch.custom_permissions)
        self.assertEqual([user.id for user in batch.get_user_custom_permissions()], [1])
        self.assertEqual([group.id for group in batch.get_group_custom_permissions()], [1])

    def test_partial_update(self):
        project = Project.objects.create()
        batch = Batch.objects.create(name='First Batch', project=project)
        url = reverse('batch-detail', args=[batch.id])
        data = {
            'name': 'Update',
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        batch = Batch.objects.get(id=batch.id)
        self.assertEqual(batch.name, 'Update')

    def test_partial_with_unallowed_field(self):
        project = Project.objects.create()
        batch = Batch.objects.create(name='First Batch', project=project)
        url = reverse('batch-detail', args=[batch.id])
        data = {
            'login_required': False,
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Cannot update through patch', response.content)

    def test_add_tasks(self):
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'project': self.project.id,
            'csv_text': 'label\nbirds\ndogs',
            'filename': 'data.csv'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        batch = Batch.objects.get(id=1)
        batch.completed = True
        batch.save()

        url = reverse('batch-tasks', args=[1])
        data = {
            'csv_text': 'label\ncats\ndeer',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(b'"new_tasks":2', response.content)
        batch = Batch.objects.get(id=1)
        self.assertEqual(batch.total_tasks(), 4)
        self.assertEqual(batch.completed, False)

    def test_add_tasks_missing_csv_text(self):
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'project': self.project.id,
            'csv_text': 'label\nbirds\ndogs',
            'filename': 'data.csv'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('batch-tasks', args=[1])
        data = {
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'This field is required', response.content)

    def test_add_tasks_missing_csv_field(self):
        url = reverse('batch-list')
        data = {
            'name': 'Batch 1',
            'project': self.project.id,
            'csv_text': 'label\nbirds\ndogs',
            'filename': 'data.csv'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('batch-tasks', args=[1])
        data = {
            'csv_text': 'heading\nbirds\ndogs',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'The missing fields are: label', response.content)
