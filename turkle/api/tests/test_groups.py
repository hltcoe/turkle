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
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Turkle User Admin')

    def test_retrieve(self):
        url = reverse('group-detail', args=[1])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Turkle User Admin')

    def test_retrieve_with_bad_id(self):
        url = reverse('group-detail', args=[99])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
