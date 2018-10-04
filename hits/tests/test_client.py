import django.test
from scripts.client import TurkleClient


class TestClient(django.test.LiveServerTestCase):
    fixtures = ['hits/tests/resources/user.json']

    def test_login_failure(self):
        client = TurkleClient(self.live_server_url, "admin", "chicken")
        self.assertFalse(client.add_user("tony", "password"))

    def test_add_user(self):
        client = TurkleClient(self.live_server_url, "admin", "password")
        self.assertTrue(client.add_user("tony", "password"))
