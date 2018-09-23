# -*- coding: utf-8 -*-
from cStringIO import StringIO
from contextlib import contextmanager
from io import BytesIO
import os
import sys

import django.test

from hits.models import Hit, HitBatch, HitTemplate
import hits.management.commands.publish_hits as publish_hits
import hits.management.commands.dump_results as dump_results


# NB: Each class subclasses the previously defined one.

class TestPublishHitsMethods(django.test.TestCase):

    def setUp(self):
        csv_text = (
            u'h0,h1\r\n'
            u'"é0",ñ0\r\n'
            u'"é1, e1",ñ1'
        )
        self.csv_file = BytesIO(csv_text.encode('utf8'))

    def test_parse_csv_file_only_newline(self):
        csv_text = (
            u'h0,h1\n'
            u'"é0",ñ0\n'
            u'"é1, e1",ñ1'
        )
        csv_file = BytesIO(csv_text.encode('utf8'))

        hit_template = HitTemplate(name='test', form="<p></p>")
        hit_template.save()
        hit_batch = HitBatch(hit_template=hit_template)
        hit_batch.save()
        hit_batch.create_hits_from_csv(csv_file)

        expect = {u"h0": u"é0", u"h1": u"ñ0"}
        actual = hit_batch.hit_set.first().input_csv_fields
        self.assertEqual(expect, actual)

        expect = {u"h0": u"é1, e1", u"h1": u"ñ1"}
        actual = hit_batch.hit_set.last().input_csv_fields
        self.assertEqual(expect, actual)

    def test_parse_csv_file(self):
        hit_template = HitTemplate(name='test', form="<p></p>")
        hit_template.save()
        hit_batch = HitBatch(hit_template=hit_template)
        hit_batch.save()
        hit_batch.create_hits_from_csv(self.csv_file)

        expect = {u"h0": u"é0", u"h1": u"ñ0"}
        actual = hit_batch.hit_set.first().input_csv_fields
        self.assertEqual(expect, actual)

        expect = {u"h0": u"é1, e1", u"h1": u"ñ1"}
        actual = hit_batch.hit_set.last().input_csv_fields
        self.assertEqual(expect, actual)


@contextmanager
def capture(command, *args, **kwargs):
    out, sys.stdout = sys.stdout, StringIO()
    err, sys.stderr = sys.stderr, StringIO()
    command(*args, **kwargs)
    sys.stdout.seek(0)
    sys.stderr.seek(0)
    yield sys.stdout.read(), sys.stderr.read()
    sys.stdout = out
    sys.stderr = err


class TestPublishHitsHandle(django.test.TestCase):
    """
    Starting with an empty database, use the publish_hits command-line script.
    """

    def setUp(self):
        args = []
        options = {
            'template_file_path': os.path.abspath('hits/tests/resources/form_1.html'),
            'csv_file_path': os.path.abspath('hits/tests/resources/form_1_vals.csv'),
            'batch_name': '',
            'template_name': '',
        }
        command = publish_hits.Command()
        with capture(command.handle, *args, **options) as result:
            self.out, self.err = result

    def test_out(self):
        self.assertEqual('', self.out)

    def test_err(self):
        self.assertEqual('Creating HITs: 1 HITs created.\n', self.err)

    def test_HitTemplate_count(self):
        """
        There should be a single HitTemplate.
        """
        self.assertEqual(1, HitTemplate.objects.count())

    def test_Hit_count(self):
        """
        There should be a single HIT.
        """
        self.assertEqual(1, Hit.objects.count())


class TestPublishHitsHandleNewline(TestPublishHitsHandle):

    def setUp(self):
        args = []
        options = {
            'template_file_path': os.path.abspath('hits/tests/resources/form_1.html'),
            'csv_file_path':
            os.path.abspath('hits/tests/resources/form_1_vals_newline_ending.csv'),
            'batch_name': '',
            'template_name': '',
        }
        command = publish_hits.Command()
        with capture(command.handle, *args, **options) as result:
            self.out, self.err = result


class TestPublishHitsHandleForm0(TestPublishHitsHandle):

    def setUp(self):
        args = []
        options = {
            'template_file_path': os.path.abspath('hits/tests/resources/form_0.html'),
            'csv_file_path': os.path.abspath('hits/tests/resources/form_0_vals.csv'),
            'batch_name': '',
            'template_name': '',
        }
        command = publish_hits.Command()
        with capture(command.handle, *args, **options) as result:
            self.out, self.err = result

    def test_Hit_fields(self):
        pass

    def test_HitTemplate_fields_name(self):
        expect = os.path.abspath('hits/tests/resources/form_0.html')
        actual = HitTemplate.objects.get(id=1).name
        self.assertEqual(expect, actual)

    def test_HitTemplate_fields_form(self):
        with open('hits/tests/resources/form_0.html') as f:
            expect = f.read().decode('utf-8')
        actual = HitTemplate.objects.get(id=1).form
        self.assertEqual(expect, actual)


class TestPublishMoreHits(TestPublishHitsHandle):
    """
    Starting with a database containing already published HITs, publishing more
    HITs should work.
    """

    def setUp(self):
        super(TestPublishMoreHits, self).setUp()
        super(TestPublishMoreHits, self).setUp()

    def test_HitTemplate_count(self):
        """
        There should still be a single HitTemplate.
        """
        self.assertEqual(1, HitTemplate.objects.count())

    def test_Hit_count(self):
        """
        There should be two Hit objects.
        """
        self.assertEqual(2, Hit.objects.count())


class TestDumpResults(TestPublishHitsHandleForm0):
    """
    Should be one Hit. complete it, then use the command line tool to dump the
    results.
    """

    def setUp(self):
        # Publish a Hit.
        super(TestDumpResults, self).setUp()

        # Mark the Hit as completed.
        hit = Hit.objects.get(id=1)

        hit.completed = True
        hit.answers = {
            u"foo": u"foo_answer",
            u"bar": u"bar_answer",
        }
        hit.save()

        # Dump the results.
        args = []
        self.options = {
            'template_file_path': os.path.abspath('hits/tests/resources/form_0.html'),
            'results_csv_file_path': os.path.abspath('temp.csv')
        }
        command = dump_results.Command()
        with capture(command.handle, *args, **self.options) as result:
            self.out, self.err = result

    def test_out(self):
        expected_out = 'Writing results for template %s to %s ...\n' % \
            (self.options['template_file_path'], self.options['results_csv_file_path'])
        self.assertEqual(expected_out, self.out)

    def test_err(self):
        self.assertEqual('', self.err)


__all__ = [
    'TestDumpResults',
    'TestPublishHitsHandle',
    'TestPublishHitsHandleNewline',
    'TestPublishHitsHandleForm0',
    'TestPublishHitsMethods',
    'TestPublishMoreHits',
]
