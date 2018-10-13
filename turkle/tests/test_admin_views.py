# -*- coding: utf-8 -*-
import os.path

import django.test
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.urls import reverse

from turkle.models import HitBatch, HitProject


class TestCancelOrPublishBatch(django.test.TestCase):
    def setUp(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        hit_project = HitProject(name='foo', html_template='<p>${foo}: ${bar}</p>')
        hit_project.save()
        self.hit_batch = HitBatch(active=False, hit_project=hit_project, name='MY_BATCH_NAME')
        self.hit_batch.save()

    def test_batch_cancel(self):
        batch_id = self.hit_batch.id
        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:cancel_batch', kwargs={'batch_id': batch_id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('turkle_admin:turkle_hitbatch_changelist'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 0)

    def test_batch_cancel_bad_batch_id(self):
        batch_id = 666
        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:cancel_batch', kwargs={'batch_id': batch_id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('turkle_admin:turkle_hitbatch_changelist'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), u'Cannot find Batch with ID 666')

    def test_batch_publish(self):
        batch_id = self.hit_batch.id
        client = django.test.Client()
        self.assertFalse(self.hit_batch.active)
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:publish_batch',
                                       kwargs={'batch_id': batch_id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('turkle_admin:turkle_hitbatch_changelist'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 0)
        self.hit_batch.refresh_from_db()
        self.assertTrue(self.hit_batch.active)

    def test_batch_publish_bad_batch_id(self):
        batch_id = 666
        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:publish_batch',
                                       kwargs={'batch_id': batch_id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('turkle_admin:turkle_hitbatch_changelist'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), u'Cannot find Batch with ID 666')


class TestHitBatchAdmin(django.test.TestCase):
    def setUp(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')

    def test_batch_add(self):
        hit_project = HitProject(name='foo', html_template='<p>${foo}: ${bar}</p>')
        hit_project.save()

        self.assertFalse(HitBatch.objects.filter(name='hit_batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        with open(os.path.abspath('turkle/tests/resources/form_1_vals.csv')) as fp:
            response = client.post(
                u'/admin/turkle/hitbatch/add/',
                {
                    'assignments_per_hit': 1,
                    'hit_project': hit_project.id,
                    'name': 'hit_batch_save',
                    'csv_file': fp
                })
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/turkle/hitbatch/1/review/')
        self.assertTrue(HitBatch.objects.filter(name='hit_batch_save').exists())
        matching_hit_batch = HitBatch.objects.filter(name='hit_batch_save').first()
        self.assertEqual(matching_hit_batch.filename, u'form_1_vals.csv')
        self.assertEqual(matching_hit_batch.total_hits(), 1)
        self.assertEqual(matching_hit_batch.allotted_assignment_time,
                         HitBatch._meta.get_field('allotted_assignment_time').get_default())

    def test_batch_add_csv_with_emoji(self):
        hit_project = HitProject(name='foo', html_template='<p>${emoji}: ${more_emoji}</p>')
        hit_project.save()

        self.assertFalse(HitBatch.objects.filter(name='hit_batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        with open(os.path.abspath('turkle/tests/resources/emoji.csv')) as fp:
            response = client.post(
                u'/admin/turkle/hitbatch/add/',
                {
                    'assignments_per_hit': 1,
                    'hit_project': hit_project.id,
                    'name': 'hit_batch_save',
                    'csv_file': fp
                })
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/turkle/hitbatch/1/review/')
        self.assertTrue(HitBatch.objects.filter(name='hit_batch_save').exists())
        matching_hit_batch = HitBatch.objects.filter(name='hit_batch_save').first()
        self.assertEqual(matching_hit_batch.filename, u'emoji.csv')

        self.assertEqual(matching_hit_batch.total_hits(), 3)
        hits = matching_hit_batch.hit_set.all()
        self.assertEqual(hits[0].input_csv_fields['emoji'], u'😀')
        self.assertEqual(hits[0].input_csv_fields['more_emoji'], u'😃')
        self.assertEqual(hits[2].input_csv_fields['emoji'], u'🤔')
        self.assertEqual(hits[2].input_csv_fields['more_emoji'], u'🤭')

    def test_batch_add_empty_allotted_assignment_time(self):
        hit_project = HitProject(name='foo', html_template='<p>${foo}: ${bar}</p>')
        hit_project.save()

        client = django.test.Client()
        client.login(username='admin', password='secret')
        with open(os.path.abspath('turkle/tests/resources/form_1_vals.csv')) as fp:
            response = client.post(
                u'/admin/turkle/hitbatch/add/',
                {
                    'allotted_assignment_time': '',
                    'assignments_per_hit': 1,
                    'hit_project': hit_project.id,
                    'name': 'hit_batch_save',
                    'csv_file': fp
                })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'error' in response.content)
        self.assertTrue(b'This field is required.' in response.content)

    def test_batch_add_missing_hit_project(self):
        hit_project = HitProject(name='foo', html_template='<p>${foo}: ${bar}</p>')
        hit_project.save()

        self.assertFalse(HitBatch.objects.filter(name='hit_batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        with open(os.path.abspath('turkle/tests/resources/form_1_vals.csv')) as fp:
            response = client.post(
                u'/admin/turkle/hitbatch/add/',
                {
                    'assignments_per_hit': 1,
                    'name': 'hit_batch_save',
                    'csv_file': fp
                })
        self.assertTrue(b'error' in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'This field is required' in response.content)

    def test_batch_add_missing_file_field(self):
        hit_project = HitProject(name='foo', html_template='<p>${emoji}: ${more_emoji}</p>')
        hit_project.save()

        self.assertFalse(HitBatch.objects.filter(name='hit_batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(
            u'/admin/turkle/hitbatch/add/',
            {
                'assignments_per_hit': 1,
                'hit_project': hit_project.id,
                'name': 'hit_batch_save',
            })
        self.assertTrue(b'error' in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'This field is required' in response.content)

    def test_batch_add_validation_extra_fields(self):
        hit_project = HitProject(name='foo', html_template='<p>${f2}</p>')
        hit_project.save()

        self.assertFalse(HitBatch.objects.filter(name='hit_batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        # CSV file has fields 'f2' and 'f3'
        with open(os.path.abspath('turkle/tests/resources/mismatched_fields.csv')) as fp:
            response = client.post(
                u'/admin/turkle/hitbatch/add/',
                {
                    'assignments_per_hit': 1,
                    'hit_project': hit_project.id,
                    'name': 'hit_batch_save',
                    'csv_file': fp
                })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'error' in response.content)
        self.assertTrue(b'extra fields' in response.content)
        self.assertTrue(b'missing fields' not in response.content)

    def test_batch_add_validation_missing_fields(self):
        hit_project = HitProject(name='foo', html_template='<p>${f1} ${f2} ${f3}</p>')
        hit_project.save()

        self.assertFalse(HitBatch.objects.filter(name='hit_batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        # CSV file has fields 'f2' and 'f3'
        with open(os.path.abspath('turkle/tests/resources/mismatched_fields.csv')) as fp:
            response = client.post(
                u'/admin/turkle/hitbatch/add/',
                {
                    'hit_project': hit_project.id,
                    'name': 'hit_batch_save',
                    'csv_file': fp
                })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'error' in response.content)
        self.assertTrue(b'extra fields' not in response.content)
        self.assertTrue(b'missing fields' in response.content)

    def test_batch_add_validation_variable_fields_per_row(self):
        hit_project = HitProject(name='foo', html_template='<p>${f1} ${f2} ${f3}</p>')
        hit_project.save()

        self.assertFalse(HitBatch.objects.filter(name='hit_batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        # CSV file has fields 'f2' and 'f3'
        with open(os.path.abspath('turkle/tests/resources/variable_fields_per_row.csv')) as fp:
            response = client.post(
                u'/admin/turkle/hitbatch/add/',
                {
                    'hit_project': hit_project.id,
                    'name': 'hit_batch_save',
                    'csv_file': fp
                })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'error' in response.content)
        self.assertTrue(b'line 2 has 2 fields' in response.content)
        self.assertTrue(b'line 4 has 4 fields' in response.content)

    def test_batch_change_get_page(self):
        self.test_batch_add()
        batch = HitBatch.objects.get(name='hit_batch_save')

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.get(
            u'/admin/turkle/hitbatch/%d/change/' % batch.id
        )
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 200)

    def test_batch_change_update(self):
        self.test_batch_add()
        batch = HitBatch.objects.get(name='hit_batch_save')

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(
            u'/admin/turkle/hitbatch/%d/change/' % batch.id,
            {
                'assignments_per_hit': 1,
                'hit_project': batch.hit_project.id,
                'name': 'hit_batch_save_modified',
            })
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/turkle/hitbatch/')
        self.assertFalse(HitBatch.objects.filter(name='hit_batch_save').exists())
        self.assertTrue(HitBatch.objects.filter(name='hit_batch_save_modified').exists())


class TestHitProject(django.test.TestCase):
    def setUp(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')

    def test_add_hit_project(self):
        self.assertEqual(HitProject.objects.filter(name='foo').count(), 0)

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('admin:turkle_hitproject_add'),
                               {
                                   'assignments_per_hit': 1,
                                   'name': 'foo',
                                   'html_template': '<p>${foo}: ${bar}</p>',
                               })
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/turkle/hitproject/')
        self.assertEqual(HitProject.objects.filter(name='foo').count(), 1)


class TestReviewBatch(django.test.TestCase):
    def test_batch_review_bad_batch_id(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        batch_id = 666
        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:review_batch', kwargs={'batch_id': batch_id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('turkle_admin:turkle_hitbatch_changelist'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), u'Cannot find Batch with ID 666')
