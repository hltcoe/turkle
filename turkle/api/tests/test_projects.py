from django.urls import reverse
from rest_framework import status

from turkle.models import Project

from . import TurkleAPITestCase


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
        self.assertTrue(b'Template does not contain any fields' in response.content)

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
        self.assertTrue(b'When login is not required to access the Project' in response.content)

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
