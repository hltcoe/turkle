import argparse
import contextlib
import io
import os
import tempfile

import django.test
import requests

from scripts.client import TurkleClient

# Integration tests for the command line scripts


class TestClient(django.test.LiveServerTestCase):
    fixtures = ['turkle/tests/resources/test_db.json']

    def setUp(self):
        self.client = TurkleClient(self.live_server_url, "admin", "password")

    def test_login_failure(self):
        # swallow stdout error messages from client
        with contextlib.redirect_stdout(io.StringIO()):
            client = TurkleClient(self.live_server_url, "admin", "chicken")
            self.assertFalse(client.add_user("tony", "password"))

    def test_add_user(self):
        self.assertTrue(self.client.add_user("tony", "password"))

    def test_add_user_invalid_username(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(self.client.add_user("tony#", "password"))

    def test_download(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.client.download(tmpdir)
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "sent-Batch_1_results.csv")))

    def test_upload(self):
        options = argparse.Namespace()
        options.login = 0
        options.num = 1
        options.project_name = "Integration Test"
        options.batch_name = "Test Batch"
        resources_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources'))
        options.template = os.path.join(resources_dir, 'sentiment.html')
        options.csv = os.path.join(resources_dir, 'sentiment.csv')

        self.assertTrue(self.client.upload(options))
        resp = requests.get(self.live_server_url)
        self.assertTrue(b"Integration Test" in resp.content)

    def test_upload_failure(self):
        options = argparse.Namespace()
        options.login = 0
        options.num = 1
        options.project_name = "Bad Test"
        options.batch_name = "Bad Batch"
        resources_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources'))
        options.template = os.path.join(resources_dir, 'sentiment.html')
        options.csv = os.path.join(resources_dir, 'sentiment_bad.csv')

        with contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(self.client.upload(options))
