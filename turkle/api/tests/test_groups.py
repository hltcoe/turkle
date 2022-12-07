from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework import status

from . import TurkleAPITestCase


class GroupsTests(TurkleAPITestCase):
    """
    Turkle is created with a default Turkle User Admin group.
    """

    def test_create(self):
        url = reverse('group-list')
        data = {
            'name': 'New Group',
            'users': [1],
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Group.objects.count(), 2)  # Turkle admin group is 1
        group = User.objects.get(username='AnonymousUser').groups.all()[0]
        self.assertEqual(group.name, 'New Group')

    def test_list(self):
        url = reverse('group-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Turkle User Admin')

    def test_retrieve(self):
        url = reverse('group-detail', args=[1])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Turkle User Admin')

    def test_retrieve_with_bad_id(self):
        url = reverse('group-detail', args=[99])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_with_name(self):
        url = reverse('group-name', args=['Turkle User Admin'])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], 1)

    def test_retrieve_with_bad_name(self):
        url = reverse('group-name', args=['Not a group'])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_users(self):
        group = Group.objects.create(name="Testing")
        user1 = User.objects.create_user('testuser1', 'password')
        user2 = User.objects.create_user('testuser2', 'password')
        url = reverse('group-users', args=[group.id])
        data = {'users': [user1.id, user2.id]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([g.id for g in User.objects.get(id=user1.id).groups.all()], [group.id])
        self.assertEqual([g.id for g in User.objects.get(id=user2.id).groups.all()], [group.id])

    def test_add_nonexistent_user(self):
        group = Group.objects.create(name="Testing")
        user1 = User.objects.create_user('testuser1', 'password')
        url = reverse('group-users', args=[group.id])
        data = {'users': [user1.id, user1.id + 1]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Unknown user id in list', response.content)
        self.assertEqual([g.id for g in User.objects.get(id=user1.id).groups.all()], [])
