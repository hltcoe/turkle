from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework import status

from . import TurkleAPITestCase


class GroupsTests(TurkleAPITestCase):
    """
    Turkle is created with a default Turkle User Admin group.
    """

    def test_create(self):
        url = reverse('groups-list-create')
        data = {
            'name': 'New Group',
            'users': ['AnonymousUser'],
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Group.objects.count(), 2)  # Turkle admin group is 1
        self.assertEqual(User.objects.get(username='AnonymousUser').groups.all()[0].name, 'New Group')

    def test_list(self):
        url = reverse('groups-list-create')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Turkle User Admin')
