import django.test
import os
import tempfile
from scripts.client import TurkleClient


class TestClient(django.test.LiveServerTestCase):
    fixtures = ['hits/tests/resources/test_db.json']

    def setUp(self):
        self.client = TurkleClient(self.live_server_url, "admin", "password")

    def test_login_failure(self):
        client = TurkleClient(self.live_server_url, "admin", "chicken")
        self.assertFalse(client.add_user("tony", "password"))

    def test_add_user(self):
        self.assertTrue(self.client.add_user("tony", "password"))

    def test_download(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.client.download(tmpdir)
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "sent-Batch_1_results.csv")))
