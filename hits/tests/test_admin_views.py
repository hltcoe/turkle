# -*- coding: utf-8 -*-
import os.path

import django.test
from django.contrib.auth.models import User

from hits.models import HitBatch, HitTemplate


class TestHitBatchAdmin(django.test.TestCase):
    def setUp(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')

    def test_batch_add(self):
        hit_template = HitTemplate(name='foo', form='<p>${foo}: ${bar}</p>')
        hit_template.save()

        self.assertFalse(HitBatch.objects.filter(name='hit_batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        with open(os.path.abspath('hits/tests/resources/form_1_vals.csv')) as fp:
            response = client.post(
                u'/admin/hits/hitbatch/add/',
                {
                    'assignments_per_hit': 1,
                    'hit_template': hit_template.id,
                    'name': 'hit_batch_save',
                    'csv_file': fp
                })
        self.assertTrue('error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/hits/hitbatch/')
        self.assertTrue(HitBatch.objects.filter(name='hit_batch_save').exists())
        matching_hit_batch = HitBatch.objects.filter(name='hit_batch_save').first()
        self.assertEqual(matching_hit_batch.filename, u'form_1_vals.csv')
        self.assertEqual(matching_hit_batch.total_hits(), 1)

    def test_batch_add_csv_with_emoji(self):
        hit_template = HitTemplate(name='foo', form='<p>${emoji}: ${more_emoji}</p>')
        hit_template.save()

        self.assertFalse(HitBatch.objects.filter(name='hit_batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        with open(os.path.abspath('hits/tests/resources/emoji.csv')) as fp:
            response = client.post(
                u'/admin/hits/hitbatch/add/',
                {
                    'assignments_per_hit': 1,
                    'hit_template': hit_template.id,
                    'name': 'hit_batch_save',
                    'csv_file': fp
                })
        self.assertTrue('error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/hits/hitbatch/')
        self.assertTrue(HitBatch.objects.filter(name='hit_batch_save').exists())
        matching_hit_batch = HitBatch.objects.filter(name='hit_batch_save').first()
        self.assertEqual(matching_hit_batch.filename, u'emoji.csv')

        self.assertEqual(matching_hit_batch.total_hits(), 3)
        hits = matching_hit_batch.hit_set.all()
        self.assertEqual(hits[0].input_csv_fields['emoji'], u'😀')
        self.assertEqual(hits[0].input_csv_fields['more_emoji'], u'😃')
        self.assertEqual(hits[2].input_csv_fields['emoji'], u'🤔')
        self.assertEqual(hits[2].input_csv_fields['more_emoji'], u'🤭')

    def test_batch_add_missing_file_field(self):
        hit_template = HitTemplate(name='foo', form='<p>${emoji}: ${more_emoji}</p>')
        hit_template.save()

        self.assertFalse(HitBatch.objects.filter(name='hit_batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(
            u'/admin/hits/hitbatch/add/',
            {
                'assignments_per_hit': 1,
                'hit_template': hit_template.id,
                'name': 'hit_batch_save',
            })
        self.assertTrue('error' in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('This field is required' in response.content)

    def test_batch_add_validation_extra_fields(self):
        hit_template = HitTemplate(name='foo', form='<p>${f2}</p>')
        hit_template.save()

        self.assertFalse(HitBatch.objects.filter(name='hit_batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        # CSV file has fields 'f2' and 'f3'
        with open(os.path.abspath('hits/tests/resources/mismatched_fields.csv')) as fp:
            response = client.post(
                u'/admin/hits/hitbatch/add/',
                {
                    'assignments_per_hit': 1,
                    'hit_template': hit_template.id,
                    'name': 'hit_batch_save',
                    'csv_file': fp
                })
        self.assertEqual(response.status_code, 200)
        self.assertTrue('error' in response.content)
        self.assertTrue('extra fields' in response.content)
        self.assertTrue('missing fields' not in response.content)

    def test_batch_add_validation_missing_fields(self):
        hit_template = HitTemplate(name='foo', form='<p>${f1} ${f2} ${f3}</p>')
        hit_template.save()

        self.assertFalse(HitBatch.objects.filter(name='hit_batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        # CSV file has fields 'f2' and 'f3'
        with open(os.path.abspath('hits/tests/resources/mismatched_fields.csv')) as fp:
            response = client.post(
                u'/admin/hits/hitbatch/add/',
                {
                    'hit_template': hit_template.id,
                    'name': 'hit_batch_save',
                    'csv_file': fp
                })
        self.assertEqual(response.status_code, 200)
        self.assertTrue('error' in response.content)
        self.assertTrue('extra fields' not in response.content)
        self.assertTrue('missing fields' in response.content)

    def test_batch_add_validation_variable_fields_per_row(self):
        hit_template = HitTemplate(name='foo', form='<p>${f1} ${f2} ${f3}</p>')
        hit_template.save()

        self.assertFalse(HitBatch.objects.filter(name='hit_batch_save').exists())

        client = django.test.Client()
        client.login(username='admin', password='secret')
        # CSV file has fields 'f2' and 'f3'
        with open(os.path.abspath('hits/tests/resources/variable_fields_per_row.csv')) as fp:
            response = client.post(
                u'/admin/hits/hitbatch/add/',
                {
                    'hit_template': hit_template.id,
                    'name': 'hit_batch_save',
                    'csv_file': fp
                })
        self.assertEqual(response.status_code, 200)
        self.assertTrue('error' in response.content)
        self.assertTrue('line 2 has 2 fields' in response.content)
        self.assertTrue('line 4 has 4 fields' in response.content)

    def test_batch_change_get_page(self):
        self.test_batch_add()
        batch = HitBatch.objects.get(name='hit_batch_save')

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.get(
            u'/admin/hits/hitbatch/%d/change/' % batch.id
        )
        self.assertTrue('error' not in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('no file selected' not in response.content)

    def test_batch_change_update(self):
        self.test_batch_add()
        batch = HitBatch.objects.get(name='hit_batch_save')

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(
            u'/admin/hits/hitbatch/%d/change/' % batch.id,
            {
                'assignments_per_hit': 1,
                'hit_template': batch.hit_template.id,
                'name': 'hit_batch_save_modified',
            })
        self.assertTrue('error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/hits/hitbatch/')
        self.assertFalse(HitBatch.objects.filter(name='hit_batch_save').exists())
        self.assertTrue(HitBatch.objects.filter(name='hit_batch_save_modified').exists())
