# -*- coding: utf-8 -*-
# hack to add unicode() to python3 for backward compatibility
try:
    unicode('')
except NameError:
    unicode = str

import django.test
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import RequestFactory, TestCase
from django.urls import reverse

from hits.models import Hit, HitAssignment, HitBatch, HitProject
from hits.views import hit_assignment


class TestAcceptHit(TestCase):
    def setUp(self):
        hit_project = HitProject(login_required=False)
        hit_project.save()
        self.hit_batch = HitBatch(hit_project=hit_project)
        self.hit_batch.save()
        self.hit = Hit(hit_batch=self.hit_batch)
        self.hit.save()

    def test_accept_unclaimed_hit(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        self.assertEqual(self.hit.hitassignment_set.count(), 0)

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.get(reverse('accept_hit',
                                      kwargs={'batch_id': self.hit_batch.id,
                                              'hit_id': self.hit.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.hit.hitassignment_set.count(), 1)
        self.assertEqual(response['Location'],
                         reverse('hit_assignment',
                                 kwargs={'hit_id': self.hit.id,
                                         'hit_assignment_id':
                                         self.hit.hitassignment_set.first().id}))

    def test_accept_unclaimed_hit_as_anon(self):
        self.assertEqual(self.hit.hitassignment_set.count(), 0)

        client = django.test.Client()
        response = client.get(reverse('accept_hit',
                                      kwargs={'batch_id': self.hit_batch.id,
                                              'hit_id': self.hit.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.hit.hitassignment_set.count(), 1)
        self.assertEqual(response['Location'],
                         reverse('hit_assignment',
                                 kwargs={'hit_id': self.hit.id,
                                         'hit_assignment_id':
                                         self.hit.hitassignment_set.first().id}))

    def test_accept_claimed_hit(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        other_user = User.objects.create_user('testuser', password='secret')
        HitAssignment(assigned_to=other_user, hit=self.hit).save()
        self.assertEqual(self.hit.hitassignment_set.count(), 1)

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.get(reverse('accept_hit',
                                      kwargs={'batch_id': self.hit_batch.id,
                                              'hit_id': self.hit.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u'The HIT with ID {} is no longer available'.format(self.hit.id))


class TestAcceptNextHit(TestCase):
    def setUp(self):
        hit_project = HitProject(login_required=False, name='foo',
                                 html_template='<p>${foo}: ${bar}</p>')
        hit_project.save()

        self.hit_batch = HitBatch(hit_project=hit_project, name='foo', filename='foo.csv')
        self.hit_batch.save()

        self.hit = Hit(
            hit_batch=self.hit_batch,
            input_csv_fields={'foo': 'fufu', 'bar': 'baba'}
        )
        self.hit.save()

    def test_accept_next_hit(self):
        user = User.objects.create_user('testuser', password='secret')
        self.assertEqual(self.hit.hitassignment_set.count(), 0)

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        # We are redirected to the hit_assignment view, but we can't predict the
        # full hit_assignment URL
        self.assertTrue('{}/assignment/'.format(self.hit.id) in response['Location'])
        self.assertEqual(self.hit.hitassignment_set.count(), 1)
        self.assertEqual(self.hit.hitassignment_set.first().assigned_to, user)

    def test_accept_next_hit_as_anon(self):
        client = django.test.Client()
        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        # We are redirected to the hit_assignment view, but we can't predict the
        # full hit_assignment URL
        self.assertTrue('{}/assignment/'.format(self.hit.id) in response['Location'])

    def test_accept_next_hit__bad_batch_id(self):
        User.objects.create_user('testuser', password='secret')
        self.assertEqual(self.hit.hitassignment_set.count(), 0)

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': 666}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        self.assertEqual(self.hit.hitassignment_set.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u'Cannot find HIT Batch with ID {}'.format(666))

    def test_accept_next_hit__no_more_hits(self):
        User.objects.create_user('testuser', password='secret')
        hit_assignment = HitAssignment(completed=True, hit=self.hit)
        hit_assignment.save()
        self.assertEqual(self.hit.hitassignment_set.count(), 1)

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        self.assertEqual(self.hit.hitassignment_set.count(), 1)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u'No more HITs available from Batch {}'.format(self.hit_batch.id))

    def test_accept_next_hit__respect_skip(self):
        hit_two = Hit(hit_batch=self.hit_batch)
        hit_two.save()

        User.objects.create_user('testuser', password='secret')
        client = django.test.Client()
        client.login(username='testuser', password='secret')

        # Per the Django docs:
        #   To modify the session and then save it, it must be stored in a variable first
        #   (because a new SessionStore is created every time this property is accessed
        #     https://docs.djangoproject.com/en/1.11/topics/testing/tools/#persistent-state
        s = client.session
        s.update({
            'skipped_hits_in_batch': {unicode(self.hit_batch.id): [unicode(self.hit.id)]}
        })
        s.save()

        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('{}/assignment/'.format(hit_two.id) in response['Location'])


class TestDownloadBatchCSV(TestCase):
    def setUp(self):
        hit_project = HitProject(name='foo', html_template='<p>${foo}: ${bar}</p>')
        hit_project.save()

        self.hit_batch = HitBatch(hit_project=hit_project, name='foo', filename='foo.csv')
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
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 200)

    def test_index_login_prompt(self):
        # Display 'Login' link when NOT logged in
        client = django.test.Client()
        response = client.get(u'/')
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Login' in response.content)

    def test_index_logout_prompt(self):
        # Display 'Logout' link and username when logged in
        client = django.test.Client()
        client.login(username='ms.admin', password='secret')
        response = client.get(u'/')
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Logout' in response.content)
        self.assertTrue(b'ms.admin' in response.content)

    def test_index_protected_template(self):
        hit_project_protected = HitProject(
            active=True,
            login_required=True,
            name='MY_TEMPLATE_NAME',
        )
        hit_project_protected.save()
        hit_batch = HitBatch(hit_project=hit_project_protected, name='MY_BATCH_NAME')
        hit_batch.save()
        Hit(hit_batch=hit_batch).save()

        anon_client = django.test.Client()
        response = anon_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'No HITs available' in response.content)
        self.assertFalse(b'MY_TEMPLATE_NAME' in response.content)
        self.assertFalse(b'MY_BATCH_NAME' in response.content)

        known_client = django.test.Client()
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        known_client.login(username='admin', password='secret')
        response = known_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'No HITs available' in response.content)
        self.assertTrue(b'MY_TEMPLATE_NAME' in response.content)
        self.assertTrue(b'MY_BATCH_NAME' in response.content)

    def test_index_unprotected_template(self):
        hit_project_unprotected = HitProject(
            active=True,
            login_required=False,
            name='MY_TEMPLATE_NAME',
        )
        hit_project_unprotected.save()
        hit_batch = HitBatch(hit_project=hit_project_unprotected, name='MY_BATCH_NAME')
        hit_batch.save()
        Hit(hit_batch=hit_batch).save()

        anon_client = django.test.Client()
        response = anon_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'No HITs available' in response.content)
        self.assertTrue(b'MY_TEMPLATE_NAME' in response.content)
        self.assertTrue(b'MY_BATCH_NAME' in response.content)

        known_client = django.test.Client()
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        known_client.login(username='admin', password='secret')
        response = known_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'No HITs available' in response.content)
        self.assertTrue(b'MY_TEMPLATE_NAME' in response.content)
        self.assertTrue(b'MY_BATCH_NAME' in response.content)


class TestHitAssignment(TestCase):

    def setUp(self):
        hit_project = HitProject(login_required=False, name='foo', html_template='<p></p>')
        hit_project.save()
        hit_batch = HitBatch(hit_project=hit_project)
        hit_batch.save()
        self.hit = Hit(hit_batch=hit_batch, input_csv_fields='{}')
        self.hit.save()
        self.hit_assignment = HitAssignment(
            assigned_to=None,
            completed=False,
            hit=self.hit
        )
        self.hit_assignment.save()

    def test_get_hit_assignment(self):
        client = django.test.Client()
        response = client.get(reverse('hit_assignment',
                                      kwargs={'hit_id': self.hit.id,
                                              'hit_assignment_id': self.hit_assignment.id}))
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 0)

    def test_get_hit_assignment_with_bad_hit_id(self):
        client = django.test.Client()
        response = client.get(reverse('hit_assignment',
                                      kwargs={'hit_id': 666,
                                              'hit_assignment_id': self.hit_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u'Cannot find HIT with ID {}'.format(666))

    def test_get_hit_assignment_with_bad_hit_assignment_id(self):
        client = django.test.Client()
        response = client.get(reverse('hit_assignment',
                                      kwargs={'hit_id': self.hit.id,
                                              'hit_assignment_id': 666}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u'Cannot find HIT Assignment with ID {}'.format(666))

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


class TestHitAssignmentIFrame(TestCase):
    def setUp(self):
        self.hit_project = HitProject(login_required=False)
        self.hit_project.save()
        hit_batch = HitBatch(hit_project=self.hit_project)
        hit_batch.save()
        self.hit = Hit(input_csv_fields={}, hit_batch=hit_batch)
        self.hit.save()
        self.hit_assignment = HitAssignment(hit=self.hit)
        self.hit_assignment.save()

    def test_template_with_submit_button(self):
        self.hit_project.html_template = \
            '<input id="my_submit_button" type="submit" value="MySubmit" />'
        self.hit_project.save()
        self.hit_project.refresh_from_db()
        self.assertTrue(self.hit_project.html_template_has_submit_button)

        client = django.test.Client()
        response = client.get(reverse('hit_assignment_iframe',
                                      kwargs={'hit_id': self.hit.id,
                                              'hit_assignment_id': self.hit_assignment.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'my_submit_button' in response.content)
        self.assertFalse(b'submitButton' in response.content)

    def test_template_without_submit_button(self):
        self.hit_project.form = '<input id="foo" type="text" value="MyText" />'
        self.hit_project.save()
        self.hit_project.refresh_from_db()
        self.assertFalse(self.hit_project.html_template_has_submit_button)

        client = django.test.Client()
        response = client.get(reverse('hit_assignment_iframe',
                                      kwargs={'hit_id': self.hit.id,
                                              'hit_assignment_id': self.hit_assignment.id}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'my_submit_button' in response.content)
        self.assertTrue(b'submitButton' in response.content)


class TestPreview(TestCase):
    def setUp(self):
        hit_project = HitProject(html_template='<p>${foo}: ${bar}</p>',
                                 login_required=False, name='foo')
        hit_project.save()
        self.hit_batch = HitBatch(filename='foo.csv', hit_project=hit_project, name='foo')
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
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u'Cannot find HIT with ID {}'.format(666))

    def test_get_preview_iframe(self):
        client = django.test.Client()
        response = client.get(reverse('preview_iframe', kwargs={'hit_id': self.hit.id}))
        self.assertEqual(response.status_code, 200)

    def test_get_preview_iframe_bad_hit_id(self):
        client = django.test.Client()
        response = client.get(reverse('preview_iframe', kwargs={'hit_id': 666}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u'Cannot find HIT with ID {}'.format(666))

    def test_preview_next_hit(self):
        client = django.test.Client()
        response = client.get(reverse('preview_next_hit', kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview', kwargs={'hit_id': self.hit.id}))

    def test_preview_next_hit_no_more_hits(self):
        self.hit.completed = True
        self.hit.save()
        client = django.test.Client()
        response = client.get(reverse('preview_next_hit', kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertTrue(u'No more HITs are available for Batch' in str(messages[0]))


class TestReturnHitAssignment(TestCase):
    def setUp(self):
        hit_project = HitProject(name='foo', html_template='<p>${foo}: ${bar}</p>')
        hit_project.save()

        hit_batch = HitBatch(hit_project=hit_project, name='foo', filename='foo.csv')
        hit_batch.save()

        self.hit = Hit(hit_batch=hit_batch)
        self.hit.save()

    def test_return_hit_assignment(self):
        user = User.objects.create_user('testuser', password='secret')

        hit_assignment = HitAssignment(
            assigned_to=user,
            hit=self.hit
        )
        hit_assignment.save()

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('return_hit_assignment',
                                      kwargs={'hit_id': self.hit.id,
                                              'hit_assignment_id': hit_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))

    def test_return_completed_hit_assignment(self):
        user = User.objects.create_user('testuser', password='secret')

        hit_assignment = HitAssignment(
            assigned_to=user,
            completed=True,
            hit=self.hit
        )
        hit_assignment.save()

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('return_hit_assignment',
                                      kwargs={'hit_id': self.hit.id,
                                              'hit_assignment_id': hit_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u"The HIT can't be returned because it has been completed")

    def test_return_hit_assignment_as_anonymous_user(self):
        hit_assignment = HitAssignment(
            assigned_to=None,
            hit=self.hit
        )
        hit_assignment.save()

        client = django.test.Client()
        response = client.get(reverse('return_hit_assignment',
                                      kwargs={'hit_id': self.hit.id,
                                              'hit_assignment_id': hit_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))

    def test_return_hit_assignment__anon_user_returns_other_users_hit(self):
        user = User.objects.create_user('testuser', password='secret')

        hit_assignment = HitAssignment(
            assigned_to=user,
            hit=self.hit
        )
        hit_assignment.save()

        client = django.test.Client()
        response = client.get(reverse('return_hit_assignment',
                                      kwargs={'hit_id': self.hit.id,
                                              'hit_assignment_id': hit_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u'The HIT you are trying to return belongs to another user')

    def test_return_hit_assignment__user_returns_anon_users_hit(self):
        User.objects.create_user('testuser', password='secret')

        hit_assignment = HitAssignment(
            assigned_to=None,
            hit=self.hit
        )
        hit_assignment.save()

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('return_hit_assignment',
                                      kwargs={'hit_id': self.hit.id,
                                              'hit_assignment_id': hit_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u'The HIT you are trying to return belongs to another user')


class TestSkipHit(TestCase):
    def setUp(self):
        hit_project = HitProject(login_required=False)
        hit_project.save()
        self.hit_batch = HitBatch(hit_project=hit_project)
        self.hit_batch.save()
        self.hit_one = Hit(hit_batch=self.hit_batch)
        self.hit_one.save()
        self.hit_two = Hit(hit_batch=self.hit_batch)
        self.hit_two.save()
        self.hit_three = Hit(hit_batch=self.hit_batch)
        self.hit_three.save()

    def test_preview_next_hit_order(self):
        client = django.test.Client()

        response = client.get(reverse('preview_next_hit', kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'hit_id': self.hit_one.id}))

        # Since no HITs have been completed or skipped, preview_next_hit redirects to same HIT
        response = client.get(reverse('preview_next_hit', kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'hit_id': self.hit_one.id}))

    def test_skip_hit(self):
        client = django.test.Client()

        # Skip hit_one
        response = client.post(reverse('skip_hit', kwargs={'batch_id': self.hit_batch.id,
                                                           'hit_id': self.hit_one.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview_next_hit',
                                                       kwargs={'batch_id': self.hit_batch.id}))

        # Verify that hit_one has been skipped
        response = client.get(reverse('preview_next_hit',
                                      kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'hit_id': self.hit_two.id}))

        # Skip hit_two
        response = client.post(reverse('skip_hit', kwargs={'batch_id': self.hit_batch.id,
                                                           'hit_id': self.hit_two.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview_next_hit',
                                                       kwargs={'batch_id': self.hit_batch.id}))

        # Verify that hit_two has been skipped
        response = client.get(reverse('preview_next_hit',
                                      kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'hit_id': self.hit_three.id}))

        # Skip hit_three
        response = client.post(reverse('skip_hit', kwargs={'batch_id': self.hit_batch.id,
                                                           'hit_id': self.hit_three.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview_next_hit',
                                                       kwargs={'batch_id': self.hit_batch.id}))

        # Verify that, with all existing HITs skipped, we have been redirected back to
        # hit_one and that info message is displayed about only skipped HITs remaining
        response = client.get(reverse('preview_next_hit',
                                      kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'hit_id': self.hit_one.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), u'Only previously skipped HITs are available')

    def test_skip_and_accept_next_hit(self):
        client = django.test.Client()

        ha_one = HitAssignment(hit=self.hit_one)
        ha_one.save()

        # Skip hit_one
        response = client.post(reverse('skip_and_accept_next_hit',
                                       kwargs={'batch_id': self.hit_batch.id,
                                               'hit_id': self.hit_one.id,
                                               'hit_assignment_id': ha_one.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accept_next_hit',
                                                       kwargs={'batch_id': self.hit_batch.id}))

        # Verify that hit_one has been skipped
        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('{}/assignment/'.format(self.hit_two.id) in response['Location'])

        # Skip hit_two
        ha_two = self.hit_two.hitassignment_set.first()
        response = client.post(reverse('skip_and_accept_next_hit',
                                       kwargs={'batch_id': self.hit_batch.id,
                                               'hit_id': self.hit_two.id,
                                               'hit_assignment_id': ha_two.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accept_next_hit',
                                                       kwargs={'batch_id': self.hit_batch.id}))

        # Verify that hit_two has been skipped
        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('{}/assignment/'.format(self.hit_three.id) in response['Location'])

        # Skip hit_three
        ha_three = self.hit_three.hitassignment_set.first()
        response = client.post(reverse('skip_and_accept_next_hit',
                                       kwargs={'batch_id': self.hit_batch.id,
                                               'hit_id': self.hit_three.id,
                                               'hit_assignment_id': ha_three.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accept_next_hit',
                                                       kwargs={'batch_id': self.hit_batch.id}))

        # Verify that, with all existing HITs skipped, we have been redirected back to
        # hit_one and that info message is displayed about only skipped HITs remaining
        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('{}/assignment/'.format(self.hit_one.id) in response['Location'])
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), u'Only previously skipped HITs are available')

        # Skip hit_one for a second time
        ha_one = self.hit_one.hitassignment_set.first()
        response = client.post(reverse('skip_and_accept_next_hit',
                                       kwargs={'batch_id': self.hit_batch.id,
                                               'hit_id': self.hit_one.id,
                                               'hit_assignment_id': ha_one.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accept_next_hit',
                                                       kwargs={'batch_id': self.hit_batch.id}))

        # Verify that hit_one has been skipped for a second time
        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.hit_batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('{}/assignment/'.format(self.hit_two.id) in response['Location'])
