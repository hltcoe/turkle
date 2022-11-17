from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from . import TurkleAPITestCase


class UsersTests(TurkleAPITestCase):
    """
    Turkle adds an anonymous user and then TurkleAPITestCase.setUp() adds a root user for authentication
    """

    def test_create(self):
        url = reverse('users-list-create')
        data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'password',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), self.root.id + 1)  # user added after the root user in setUp()
        user = User.objects.get(username='testuser')
        self.assertEqual(user.first_name, 'Test')
        self.assertTrue(user.check_password('password'))

    def test_list(self):
        url = reverse('users-list-create')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['username'], 'AnonymousUser')
        self.assertEqual(response.data[1]['username'], 'root')

    def test_retrieve(self):
        url = reverse('users-details', args=[1])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'AnonymousUser')

    def test_retrieve_with_bad_id(self):
        url = reverse('users-details', args=[99])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_single_field(self):
        url = reverse('users-details', args=[1])
        response = self.client.patch(url, {'first_name': 'Ted'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'AnonymousUser')
        self.assertEqual(response.data['first_name'], 'Ted')

    def test_patch_more_than_one_field(self):
        url = reverse('users-details', args=[1])
        response = self.client.patch(url, {'first_name': 'Ted', 'last_name': 'Roosevelt'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'AnonymousUser')
        self.assertEqual(response.data['first_name'], 'Ted')
        self.assertEqual(response.data['last_name'], 'Roosevelt')

    def test_put_all_required_fields(self):
        url = reverse('users-details', args=[1])
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
        url = reverse('users-details', args=[1])
        data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
