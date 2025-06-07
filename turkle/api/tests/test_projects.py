import json

from django.contrib.auth.models import User
from django.urls import reverse
import guardian.shortcuts
from rest_framework import status

from turkle.models import Batch, Project

from . import TurkleAPITestCase


def create_project(client):
    url = reverse('project-list')
    html = '<html><label>${field1}</label><input type="text"></html>'
    data = {
        'name': 'Project 1',
        'html_template': html,
        'filename': 'template.html',
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED


class ProjectsTests(TurkleAPITestCase):
    def test_create(self):
        url = reverse('project-list')
        html = '<html><label>${field1}</label><input type="text"><input type="submit"></html>'
        data = {
            'name': 'Project 1',
            'html_template': html,
            'filename': 'template.html'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        project = Project.objects.get(id=1)
        self.assertEqual(project.name, 'Project 1')
        self.assertEqual(set(project.fieldnames.keys()), {'field1'})
        self.assertTrue(project.html_template_has_submit_button)

    def test_create_with_empty_html_template(self):
        url = reverse('project-list')
        data = {
            'name': 'Project 1',
            'html_template': '',
            'filename': 'template.html'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, b'{"html_template":["This field may not be blank."]}')

    def test_create_with_missing_html_template(self):
        url = reverse('project-list')
        data = {
            'name': 'Project 1',
            'filename': 'template.html'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, b'{"html_template":["This field is required."]}')

    def test_create_with_missing_input(self):
        url = reverse('project-list')
        data = {
            'name': 'Project 1',
            'html_template': '<html></html>',
            'filename': 'template.html'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Template does not contain any fields', response.content)

    def test_create_with_create_date_set(self):
        # the field gets ignored because it is read-only
        date = '2022-11-14T14:12:30.974120+00:00'
        url = reverse('project-list')
        html = '<html><label>${field1}</label><input type="text"></html>'
        data = {
            'name': 'Project 1',
            'html_template': html,
            'filename': 'template.html',
            'created_at': date
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        project = Project.objects.get(id=1)
        self.assertNotEqual(project.created_at.isoformat(), date)

    def test_create_with_incompatible_login_required_and_assignments_per_task(self):
        url = reverse('project-list')
        html = '<html><label>${field1}</label><input type="text"></html>'
        data = {
            'name': 'Project 1',
            'html_template': html,
            'filename': 'template.html',
            'login_required': False,
            'assignments_per_task': 2
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'When login is not required to access the Project', response.content)

    def test_create_with_two_assignments_per_task_but_login_not_set(self):
        # default is login required
        url = reverse('project-list')
        html = '<html><label>${field1}</label><input type="text"></html>'
        data = {
            'name': 'Project 1',
            'html_template': html,
            'filename': 'template.html',
            'assignments_per_task': 2
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_setting_permissions(self):
        create_project(self.client)
        url = reverse('project-permissions-list', args=[1])
        data = {
            'users': [1],
            'groups': [1],
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(id=1)
        self.assertTrue(project.custom_permissions)
        self.assertEqual([user.id for user in project.get_user_custom_permissions()], [1])
        self.assertEqual([group.id for group in project.get_group_custom_permissions()], [1])

    def test_setting_permissions_with_bad_user(self):
        create_project(self.client)
        url = reverse('project-permissions-list', args=[1])
        data = {
            'users': [99],
            'groups': [],
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        msg = json.loads(response.content)['users'][0]
        self.assertEqual('User with id 99 does not exist', msg)

    def test_setting_permissions_with_bad_group(self):
        create_project(self.client)
        url = reverse('project-permissions-list', args=[1])
        data = {
            'users': [1],
            'groups': [99],
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        msg = json.loads(response.content)['groups'][0]
        self.assertEqual('Group with id 99 does not exist', msg)

    def test_adding_permissions(self):
        user1 = User.objects.create_user('testuser1', 'password')
        user2 = User.objects.create_user('testuser2', 'password')
        create_project(self.client)
        project = Project.objects.get(id=1)
        project.custom_permissions = True
        project.save()
        guardian.shortcuts.assign_perm('can_work_on', user1, project)
        url = reverse('project-permissions-list', args=[1])
        data = {
            'users': [user2.id],
            'groups': [],
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(project.custom_permissions)
        self.assertEqual([user.id for user in project.get_user_custom_permissions()],
                         [user1.id, user2.id])

    def test_replacing_permissions(self):
        user1 = User.objects.create_user('testuser1', 'password')
        user2 = User.objects.create_user('testuser2', 'password')
        create_project(self.client)
        project = Project.objects.get(id=1)
        project.custom_permissions = True
        project.save()
        guardian.shortcuts.assign_perm('can_work_on', user1, project)
        url = reverse('project-permissions-list', args=[1])
        data = {
            'users': [user2.id],
            'groups': [],
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(project.custom_permissions)
        self.assertEqual([user.id for user in project.get_user_custom_permissions()], [user2.id])

    def test_partial_update(self):
        create_project(self.client)
        url = reverse('project-detail', args=[1])
        data = {
            'name': 'Update'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project = Project.objects.get(id=1)
        self.assertEqual(project.name, 'Update')

    def test_partial_update_conflict_on_assignments(self):
        create_project(self.client)
        project = Project.objects.get(id=1)
        project.login_required = False
        project.save()
        url = reverse('project-detail', args=[1])
        data = {
            'assignments_per_task': 2
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_login_required(self):
        create_project(self.client)
        url = reverse('project-detail', args=[1])
        data = {
            'login_required': False
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project = Project.objects.get(id=1)
        self.assertEqual(project.login_required, False)

    def test_include_batches_for_project(self):
        project = Project.objects.create(name='Test')
        batch = Batch.objects.create(project=project)
        url = reverse('project-detail', args=[project.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content)['batches'], [batch.id])

    def test_list_batches_for_project(self):
        project = Project.objects.create(name='Test')
        Batch.objects.create(name='Batch Test', project=project)
        url = reverse('project-batches', args=[project.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(json.loads(response.content)['results']), 1)
