# -*- coding: utf-8 -*-
import os.path

import django.test
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.urls import reverse

from turkle.models import Batch, Project


class TestCancelOrPublishBatch(django.test.TestCase):
    def setUp(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        project = Project(name='foo', html_template='<p>${foo}: ${bar}</p>')
        project.save()
        self.batch = Batch(active=False, project=project, name='MY_BATCH_NAME')
        self.batch.save()

    def test_batch_cancel(self):
        batch_id = self.batch.id
        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:cancel_batch', kwargs={'batch_id': batch_id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('turkle_admin:turkle_batch_changelist'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 0)

    def test_batch_cancel_bad_batch_id(self):
        batch_id = 666
        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:cancel_batch', kwargs={'batch_id': batch_id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('turkle_admin:turkle_batch_changelist'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), u'Cannot find Batch with ID 666')

    def test_batch_publish(self):
        batch_id = self.batch.id
        client = django.test.Client()
        self.assertFalse(self.batch.active)
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:publish_batch',
                                       kwargs={'batch_id': batch_id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('turkle_admin:turkle_batch_changelist'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 0)
        self.batch.refresh_from_db()
        self.assertTrue(self.batch.active)

    def test_batch_publish_bad_batch_id(self):
        batch_id = 666
        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:publish_batch',
                                       kwargs={'batch_id': batch_id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('turkle_admin:turkle_batch_changelist'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), u'Cannot find Batch with ID 666')


class TestBatchAdmin(django.test.TestCase):
    def setUp(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')

    def test_batch_add(self):
        project = Project(name='foo', html_template='<p>${foo}: ${bar}</p>')
        project.save()

        self.assertFalse(Batch.objects.filter(name='batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        with open(os.path.abspath('turkle/tests/resources/form_1_vals.csv')) as fp:
            response = client.post(
                u'/admin/turkle/batch/add/',
                {
                    'assignments_per_hit': 1,
                    'project': project.id,
                    'name': 'batch_save',
                    'csv_file': fp
                })
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/turkle/batch/1/review/')
        self.assertTrue(Batch.objects.filter(name='batch_save').exists())
        matching_batch = Batch.objects.filter(name='batch_save').first()
        self.assertEqual(matching_batch.filename, u'form_1_vals.csv')
        self.assertEqual(matching_batch.total_hits(), 1)
        self.assertEqual(matching_batch.allotted_assignment_time,
                         Batch._meta.get_field('allotted_assignment_time').get_default())

    def test_batch_add_csv_with_emoji(self):
        project = Project(name='foo', html_template='<p>${emoji}: ${more_emoji}</p>')
        project.save()

        self.assertFalse(Batch.objects.filter(name='batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        with open(os.path.abspath('turkle/tests/resources/emoji.csv')) as fp:
            response = client.post(
                u'/admin/turkle/batch/add/',
                {
                    'assignments_per_hit': 1,
                    'project': project.id,
                    'name': 'batch_save',
                    'csv_file': fp
                })
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/turkle/batch/1/review/')
        self.assertTrue(Batch.objects.filter(name='batch_save').exists())
        matching_batch = Batch.objects.filter(name='batch_save').first()
        self.assertEqual(matching_batch.filename, u'emoji.csv')

        self.assertEqual(matching_batch.total_hits(), 3)
        hits = matching_batch.hit_set.all()
        self.assertEqual(hits[0].input_csv_fields['emoji'], u'😀')
        self.assertEqual(hits[0].input_csv_fields['more_emoji'], u'😃')
        self.assertEqual(hits[2].input_csv_fields['emoji'], u'🤔')
        self.assertEqual(hits[2].input_csv_fields['more_emoji'], u'🤭')

    def test_batch_add_empty_allotted_assignment_time(self):
        project = Project(name='foo', html_template='<p>${foo}: ${bar}</p>')
        project.save()

        client = django.test.Client()
        client.login(username='admin', password='secret')
        with open(os.path.abspath('turkle/tests/resources/form_1_vals.csv')) as fp:
            response = client.post(
                u'/admin/turkle/batch/add/',
                {
                    'allotted_assignment_time': '',
                    'assignments_per_hit': 1,
                    'project': project.id,
                    'name': 'batch_save',
                    'csv_file': fp
                })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'error' in response.content)
        self.assertTrue(b'This field is required.' in response.content)

    def test_batch_add_missing_project(self):
        project = Project(name='foo', html_template='<p>${foo}: ${bar}</p>')
        project.save()

        self.assertFalse(Batch.objects.filter(name='batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        with open(os.path.abspath('turkle/tests/resources/form_1_vals.csv')) as fp:
            response = client.post(
                u'/admin/turkle/batch/add/',
                {
                    'assignments_per_hit': 1,
                    'name': 'batch_save',
                    'csv_file': fp
                })
        self.assertTrue(b'error' in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'This field is required' in response.content)

    def test_batch_add_missing_file_field(self):
        project = Project(name='foo', html_template='<p>${emoji}: ${more_emoji}</p>')
        project.save()

        self.assertFalse(Batch.objects.filter(name='batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(
            u'/admin/turkle/batch/add/',
            {
                'assignments_per_hit': 1,
                'project': project.id,
                'name': 'batch_save',
            })
        self.assertTrue(b'error' in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'This field is required' in response.content)

    def test_batch_add_validation_extra_fields(self):
        project = Project(name='foo', html_template='<p>${f2}</p>')
        project.save()

        self.assertFalse(Batch.objects.filter(name='batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        # CSV file has fields 'f2' and 'f3'
        with open(os.path.abspath('turkle/tests/resources/mismatched_fields.csv')) as fp:
            response = client.post(
                u'/admin/turkle/batch/add/',
                {
                    'assignments_per_hit': 1,
                    'project': project.id,
                    'name': 'batch_save',
                    'csv_file': fp
                })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'error' in response.content)
        self.assertTrue(b'extra fields' in response.content)
        self.assertTrue(b'missing fields' not in response.content)

    def test_batch_add_validation_missing_fields(self):
        project = Project(name='foo', html_template='<p>${f1} ${f2} ${f3}</p>')
        project.save()

        self.assertFalse(Batch.objects.filter(name='batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        # CSV file has fields 'f2' and 'f3'
        with open(os.path.abspath('turkle/tests/resources/mismatched_fields.csv')) as fp:
            response = client.post(
                u'/admin/turkle/batch/add/',
                {
                    'project': project.id,
                    'name': 'batch_save',
                    'csv_file': fp
                })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'error' in response.content)
        self.assertTrue(b'extra fields' not in response.content)
        self.assertTrue(b'missing fields' in response.content)

    def test_batch_add_validation_variable_fields_per_row(self):
        project = Project(name='foo', html_template='<p>${f1} ${f2} ${f3}</p>')
        project.save()

        self.assertFalse(Batch.objects.filter(name='batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        # CSV file has fields 'f2' and 'f3'
        with open(os.path.abspath('turkle/tests/resources/variable_fields_per_row.csv')) as fp:
            response = client.post(
                u'/admin/turkle/batch/add/',
                {
                    'project': project.id,
                    'name': 'batch_save',
                    'csv_file': fp
                })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'error' in response.content)
        self.assertTrue(b'line 2 has 2 fields' in response.content)
        self.assertTrue(b'line 4 has 4 fields' in response.content)

    def test_batch_change_get_page(self):
        self.test_batch_add()
        batch = Batch.objects.get(name='batch_save')

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.get(
            u'/admin/turkle/batch/%d/change/' % batch.id
        )
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 200)

    def test_batch_change_update(self):
        self.test_batch_add()
        batch = Batch.objects.get(name='batch_save')

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(
            u'/admin/turkle/batch/%d/change/' % batch.id,
            {
                'assignments_per_hit': 1,
                'project': batch.project.id,
                'name': 'batch_save_modified',
            })
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/turkle/batch/')
        self.assertFalse(Batch.objects.filter(name='batch_save').exists())
        self.assertTrue(Batch.objects.filter(name='batch_save_modified').exists())


class TestProject(django.test.TestCase):
    def setUp(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')

    def test_add_project(self):
        self.assertEqual(Project.objects.filter(name='foo').count(), 0)

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('admin:turkle_project_add'),
                               {
                                   'assignments_per_hit': 1,
                                   'name': 'foo',
                                   'html_template': '<p>${foo}: ${bar}</p>',
                               })
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/turkle/project/')
        self.assertEqual(Project.objects.filter(name='foo').count(), 1)


class TestReviewBatch(django.test.TestCase):
    def test_batch_review_bad_batch_id(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        batch_id = 666
        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:review_batch', kwargs={'batch_id': batch_id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('turkle_admin:turkle_batch_changelist'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), u'Cannot find Batch with ID 666')
