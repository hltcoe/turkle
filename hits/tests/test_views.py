# -*- coding: utf-8 -*-
import django.test
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.auth.models import User
from django.urls import reverse

from hits.models import Hit, HitAssignment, HitBatch, HitTemplate
from hits.views import hit_assignment


class TestDownloadBatchCSV(django.test.TestCase):
    def setUp(self):
        hit_template = HitTemplate(name='foo', form='<p>${foo}: ${bar}</p>')
        hit_template.save()

        self.hit_batch = HitBatch(hit_template=hit_template, name='foo', filename='foo.csv')
        self.hit_batch.save()

        hit = Hit(
            hit_batch=self.hit_batch,
            input_csv_fields={'foo': 'fufu', 'bar': 'baba'}
        )
        hit.save()
        HitAssignment(
            answers={'a1': 'sauce'},
            assigned_to=None,
            completed=True,
            hit=hit
        ).save()

    def test_get_as_admin(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')

        client = django.test.Client()
        client.login(username='admin', password='secret')
        download_url = reverse('download_batch_csv', kwargs={'batch_id': self.hit_batch.id})
        response = client.get(download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'),
                         'attachment; filename="%s"' % self.hit_batch.csv_results_filename())

    def test_get_as_rando(self):
        client = django.test.Client()
        client.login(username='admin', password='secret')
        download_url = reverse('download_batch_csv', kwargs={'batch_id': self.hit_batch.id})
        response = client.get(download_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/login/?next=%s' % download_url)


class TestIndex(django.test.TestCase):
    def setUp(self):
        User.objects.create_superuser('ms.admin', 'foo@bar.foo', 'secret')

    def test_get_index(self):
        client = django.test.Client()
        response = client.get(u'/')
        self.assertTrue('error' not in response.content)
        self.assertEqual(response.status_code, 200)

    def test_index_login_prompt(self):
        # Display 'Login' link when NOT logged in
        client = django.test.Client()
        response = client.get(u'/')
        self.assertTrue('error' not in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Login' in response.content)

    def test_index_logout_prompt(self):
        # Display 'Logout' link and username when logged in
        client = django.test.Client()
        client.login(username='ms.admin', password='secret')
        response = client.get(u'/')
        self.assertTrue('error' not in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Logout' in response.content)
        self.assertTrue('ms.admin' in response.content)

    def test_index_protected_template(self):
        hit_template_protected = HitTemplate(
            active=True,
            login_required=True,
            name='MY_TEMPLATE_NAME',
        )
        hit_template_protected.save()
        hit_batch = HitBatch(hit_template=hit_template_protected, name='MY_BATCH_NAME')
        hit_batch.save()
        Hit(hit_batch=hit_batch).save()

        anon_client = django.test.Client()
        response = anon_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('No HITs available' in response.content)
        self.assertFalse('MY_TEMPLATE_NAME' in response.content)
        self.assertFalse('MY_BATCH_NAME' in response.content)

        known_client = django.test.Client()
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        known_client.login(username='admin', password='secret')
        response = known_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse('No HITs available' in response.content)
        self.assertTrue('MY_TEMPLATE_NAME' in response.content)
        self.assertTrue('MY_BATCH_NAME' in response.content)

    def test_index_unprotected_template(self):
        hit_template_unprotected = HitTemplate(
            active=True,
            login_required=False,
            name='MY_TEMPLATE_NAME',
        )
        hit_template_unprotected.save()
        hit_batch = HitBatch(hit_template=hit_template_unprotected, name='MY_BATCH_NAME')
        hit_batch.save()
        Hit(hit_batch=hit_batch).save()

        anon_client = django.test.Client()
        response = anon_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse('No HITs available' in response.content)
        self.assertTrue('MY_TEMPLATE_NAME' in response.content)
        self.assertTrue('MY_BATCH_NAME' in response.content)

        known_client = django.test.Client()
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        known_client.login(username='admin', password='secret')
        response = known_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse('No HITs available' in response.content)
        self.assertTrue('MY_TEMPLATE_NAME' in response.content)
        self.assertTrue('MY_BATCH_NAME' in response.content)


class TestHitAssignment(django.test.TestCase):

    def setUp(self):
        hit_template = HitTemplate(name='foo', form='<p></p>')
        hit_template.save()
        hit_batch = HitBatch(hit_template=hit_template)
        hit_batch.save()
        self.hit = Hit(hit_batch=hit_batch, input_csv_fields='{}')
        self.hit.save()
        self.hit_assignment = HitAssignment(
            assigned_to=None,
            completed=False,
            hit=self.hit
        )
        self.hit_assignment.save()

    def test_0(self):
        post_request = RequestFactory().post(
            u'/hits/%d/assignment/%d/' % (self.hit.id, self.hit_assignment.id),
            {u'foo': u'bar'}
        )
        post_request.csrf_processing_done = True
        hit_assignment(post_request, self.hit.id, self.hit_assignment.id)
        ha = HitAssignment.objects.get(id=self.hit_assignment.id)

        expect = {u'foo': u'bar'}
        actual = ha.answers
        self.assertEqual(expect, actual)


class TestPreview(django.test.TestCase):
    def setUp(self):
        hit_template = HitTemplate(form='<p>${foo}: ${bar}</p>', login_required=False, name='foo')
        hit_template.save()
        self.hit_batch = HitBatch(filename='foo.csv', hit_template=hit_template, name='foo')
        self.hit_batch.save()
        self.hit = Hit(
            hit_batch=self.hit_batch,
            input_csv_fields={'foo': 'fufu', 'bar': 'baba'},
        )
        self.hit.save()

    def test_get_preview(self):
        client = django.test.Client()
        response = client.get(reverse('preview', kwargs={'hit_id': self.hit.id}))
        self.assertEqual(response.status_code, 200)

    def test_get_preview_bad_hit_id(self):
        client = django.test.Client()
        response = client.get(reverse('preview', kwargs={'hit_id': 666}))
        self.assertEqual(response.status_code, 404)

    def test_get_preview_iframe(self):
        client = django.test.Client()
        response = client.get(reverse('preview_iframe', kwargs={'hit_id': self.hit.id}))
        self.assertEqual(response.status_code, 200)

    def test_get_preview_iframe_bad_hit_id(self):
        client = django.test.Client()
        response = client.get(reverse('preview_iframe', kwargs={'hit_id': 666}))
        self.assertEqual(response.status_code, 404)

    def test_preview_next_hit(self):
        client = django.test.Client()
        client.login()
        response = client.get(reverse('preview_next_hit', kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview', kwargs={'hit_id': self.hit.id}))


# This was grabbed from
# http://djangosnippets.org/snippets/963/
class RequestFactory(django.test.Client):
    """
    Class that lets you create mock Request objects for use in testing.

    Usage:

    rf = RequestFactory()
    get_request = rf.get('/hello/')
    post_request = rf.post('/submit/', {'foo': 'bar'})

    This class re-uses the django.test.client.Client interface, docs here:
    http://www.djangoproject.com/documentation/testing/#the-test-client

    Once you have a request object you can pass it to any view function,
    just as if that view had been hooked up using a URLconf.

    """
    def request(self, **request):
        """
        Similar to parent class, but returns the request object as soon as it
        has created it.
        """
        environ = {
            'HTTP_COOKIE': self.cookies,
            'PATH_INFO': '/',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '',
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': 80,
            'SERVER_PROTOCOL': 'HTTP/1.1',
        }
        environ.update(self.defaults)
        environ.update(request)
        rqst = WSGIRequest(environ)
        rqst.user = None
        return rqst


__all__ = (
    'RequestFactory',
)
