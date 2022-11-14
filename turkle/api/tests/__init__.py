from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class TurkleAPITestCase(APITestCase):
    def setUp(self):
        self.root, created = User.objects.get_or_create(username='root')
        if created:
            self.root.is_admin = True
            self.root.save()
            Token.objects.create(user=self.root)
        self.token = Token.objects.get(user__username='root')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
