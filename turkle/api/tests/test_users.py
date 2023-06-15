from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from . import TurkleAPITestCase


class UsersTests(TurkleAPITestCase):
    """
    Turkle adds an anonymous user and TurkleAPITestCase.setUp() adds a root user for authentication
    """

    def test_create(self):
        url = reverse('user-list')
        data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'password',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # user added after the root user in setUp()
        self.assertEqual(User.objects.count(), self.root.id + 1)
        user = User.objects.get(username='testuser')
        self.assertEqual(user.first_name, 'Test')
        self.assertTrue(user.check_password('password'))

    def test_list(self):
        url = reverse('user-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['username'], 'AnonymousUser')
        self.assertEqual(response.data['results'][1]['username'], 'root')

    def test_retrieve(self):
        url = reverse('user-detail', args=[1])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'AnonymousUser')

    def test_retrieve_with_bad_id(self):
        url = reverse('user-detail', args=[99])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_single_field(self):
        url = reverse('user-detail', args=[1])
        response = self.client.patch(url, {'first_name': 'Ted'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'AnonymousUser')
        self.assertEqual(response.data['first_name'], 'Ted')

    def test_patch_more_than_one_field(self):
        url = reverse('user-detail', args=[1])
        data = {'first_name': 'Ted', 'last_name': 'Roosevelt'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'AnonymousUser')
        self.assertEqual(response.data['first_name'], 'Ted')
        self.assertEqual(response.data['last_name'], 'Roosevelt')

    def test_patch_password(self):
        url = reverse('user-detail', args=[1])
        data = {'password': 'qwerty'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(id=1)
        self.assertTrue(user.check_password('qwerty'))

    def test_put_all_required_fields(self):
        url = reverse('user-detail', args=[1])
        data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'qwerty',
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
        user = User.objects.get(username='testuser')
        self.assertTrue(user.check_password('qwerty'))

    def test_put_missing_required_field(self):
        url = reverse('user-detail', args=[1])
        data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_with_username(self):
        url = reverse('user-username', args=['AnonymousUser'])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 1)

    def test_retrieve_with_bad_username(self):
        url = reverse('user-username', args=['GhostUser'])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
