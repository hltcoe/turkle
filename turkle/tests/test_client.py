from __future__ import print_function

import argparse
import django.test
import os
import requests
import sys
import tempfile
import warnings

from scripts.client import TurkleClient

# Integration tests for the command line scripts


# monkey patch tempfile for python 2.7
class TemporaryDirectory(object):
    """Create and return a temporary directory.  This has the same
    behavior as mkdtemp but can be used as a context manager.  For
    example:

        with TemporaryDirectory() as tmpdir:
            ...

    Upon exiting the context, the directory and everything contained
    in it are removed.
    """

    def __init__(self, suffix="", prefix="tmp", dir=None):
        self._closed = False
        self.name = None
        self.name = tempfile.mkdtemp(suffix, prefix, dir)

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, self.name)

    def __enter__(self):
        return self.name

    def cleanup(self, _warn=False):
        if self.name and not self._closed:
            try:
                self._rmtree(self.name)
            except (TypeError, AttributeError) as ex:
                # Issue #10188: Emit a warning on stderr
                # if the directory could not be cleaned
                # up due to missing globals
                if "None" not in str(ex):
                    raise
                print("ERROR: {!r} while cleaning up {!r}".format(ex, self,),
                      file=sys.stderr)
                return
            self._closed = True
            if _warn:
                self._warn("Implicitly cleaning up {!r}".format(self))

    def __exit__(self, exc, value, tb):
        self.cleanup()

    def __del__(self):
        self.cleanup(_warn=True)

    # XXX (ncoghlan): The following code attempts to make
    # this class tolerant of the module nulling out process
    # that happens during CPython interpreter shutdown
    # Alas, it doesn't actually manage it. See issue #10188
    _listdir = staticmethod(os.listdir)
    _path_join = staticmethod(os.path.join)
    _isdir = staticmethod(os.path.isdir)
    _islink = staticmethod(os.path.islink)
    _remove = staticmethod(os.remove)
    _rmdir = staticmethod(os.rmdir)
    _warn = warnings.warn

    def _rmtree(self, path):
        # Essentially a stripped down version of shutil.rmtree.  We can't
        # use globals because they may be None'ed out at shutdown.
        for name in self._listdir(path):
            fullname = self._path_join(path, name)
            try:
                isdir = self._isdir(fullname) and not self._islink(fullname)
            except OSError:
                isdir = False
            if isdir:
                self._rmtree(fullname)
            else:
                try:
                    self._remove(fullname)
                except OSError:
                    pass
        try:
            self._rmdir(path)
        except OSError:
            pass


if sys.version_info[0] == 2:
    tempfile.TemporaryDirectory = TemporaryDirectory


class TestClient(django.test.LiveServerTestCase):
    fixtures = ['turkle/tests/resources/test_db.json']

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

        self.assertFalse(self.client.upload(options))
