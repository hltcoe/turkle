from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from . import TurkleAPITestCase


class UsersTests(TurkleAPITestCase):
    """
    Turkle adds an anonymous user and then TurkleAPITestCase.setUp() adds a root user for authentication
    """

    def test_create(self):
        url = reverse('users-list')
        data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'password',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), self.root.id + 1)  # user added after the root user in setUp()
        self.assertEqual(User.objects.get(username='testuser').first_name, 'Test')

    def test_list(self):
        url = reverse('users-list')
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

    def test_update(self):
        url = reverse('users-details', args=[1])
        response = self.client.patch(url, {'first_name': 'Ted'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'AnonymousUser')
        self.assertEqual(response.data['first_name'], 'Ted')

    def test_delete(self):
        url = reverse('users-details', args=[1])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_with_username(self):
        url = reverse('users-username', args=['AnonymousUser'])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 1)

    def test_retrieve_with_bad_username(self):
        url = reverse('users-username', args=['GhostUser'])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
