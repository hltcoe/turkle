import django.test
from subprocess import Popen, PIPE
#from hits.management.commands import dump_results, publish_hits


class TestManagementCommands(django.test.TestCase):
    def setUp(self):
        publish_hits_cmd = [
            'python', 'manage.py', 'publish_hits',
            'hits/tests/resources/form_0.html',
            'hits/tests/resources/form_0_vals.csv'
        ]
        p = Popen(publish_hits_cmd, stdout=PIPE, stderr=PIPE)
        self.results = p.communicate()


class TestDumpResults(TestManagementCommands):
    pass


class TestPublishHits(TestManagementCommands):

    def test_out(self):
        out, __ = self.results
        self.assertEqual('', out)

    def test_err(self):
        __, err = self.results
        self.assertEqual('Creating HITs: 1 HITs created.\n', err)
