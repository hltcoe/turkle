# -*- coding: utf-8 -*-
# hack to add unicode() to python3 for backward compatibility
try:
    unicode('')
except NameError:
    unicode = str
import datetime

import django.test
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from turkle.models import Hit, HitAssignment, Batch, Project


class TestAcceptHit(TestCase):
    def setUp(self):
        project = Project(login_required=False)
        project.save()
        self.batch = Batch(project=project)
        self.batch.save()
        self.hit = Hit(batch=self.batch)
        self.hit.save()

    def test_accept_unclaimed_hit(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        self.assertEqual(self.hit.hitassignment_set.count(), 0)

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.get(reverse('accept_hit',
                                      kwargs={'batch_id': self.batch.id,
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
                                      kwargs={'batch_id': self.batch.id,
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
                                      kwargs={'batch_id': self.batch.id,
                                              'hit_id': self.hit.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u'The Task with ID {} is no longer available'.format(self.hit.id))


class TestAcceptNextHit(TestCase):
    def setUp(self):
        project = Project(login_required=False, name='foo',
                          html_template='<p>${foo}: ${bar}</p>')
        project.save()

        self.batch = Batch(project=project, name='foo', filename='foo.csv')
        self.batch.save()

        self.hit = Hit(
            batch=self.batch,
            input_csv_fields={'foo': 'fufu', 'bar': 'baba'}
        )
        self.hit.save()

    def test_accept_next_hit(self):
        user = User.objects.create_user('testuser', password='secret')
        self.assertEqual(self.hit.hitassignment_set.count(), 0)

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        # We are redirected to the hit_assignment view, but we can't predict the
        # full hit_assignment URL
        self.assertTrue('{}/assignment/'.format(self.hit.id) in response['Location'])
        self.assertEqual(self.hit.hitassignment_set.count(), 1)
        self.assertEqual(self.hit.hitassignment_set.first().assigned_to, user)

    def test_accept_next_hit_as_anon(self):
        client = django.test.Client()
        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.batch.id}))
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
                         u'Cannot find Task Batch with ID {}'.format(666))

    def test_accept_next_hit__no_more_hits(self):
        User.objects.create_user('testuser', password='secret')
        hit_assignment = HitAssignment(completed=True, hit=self.hit)
        hit_assignment.save()
        self.assertEqual(self.hit.hitassignment_set.count(), 1)

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        self.assertEqual(self.hit.hitassignment_set.count(), 1)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u'No more Tasks available from Batch {}'.format(self.batch.id))

    def test_accept_next_hit__respect_skip(self):
        hit_two = Hit(batch=self.batch)
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
            'skipped_hits_in_batch': {unicode(self.batch.id): [unicode(self.hit.id)]}
        })
        s.save()

        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('{}/assignment/'.format(hit_two.id) in response['Location'])


class TestDownloadBatchCSV(TestCase):
    def setUp(self):
        project = Project(name='foo', html_template='<p>${foo}: ${bar}</p>')
        project.save()

        self.batch = Batch(project=project, name='foo', filename='foo.csv')
        self.batch.save()

        hit = Hit(
            batch=self.batch,
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
        download_url = reverse('download_batch_csv', kwargs={'batch_id': self.batch.id})
        response = client.get(download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'),
                         'attachment; filename="%s"' % self.batch.csv_results_filename())

    def test_get_as_rando(self):
        client = django.test.Client()
        client.login(username='admin', password='secret')
        download_url = reverse('download_batch_csv', kwargs={'batch_id': self.batch.id})
        response = client.get(download_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/login/?next=%s' % download_url)


class TestExpireAbandonedAssignments(django.test.TestCase):
    def test_expire_abandoned_assignments(self):
        t = timezone.now()
        dt = datetime.timedelta(hours=2)
        past = t - dt

        project = Project(login_required=False)
        project.save()
        batch = Batch(
            allotted_assignment_time=1,
            project=project
        )
        batch.save()
        hit = Hit(batch=batch)
        hit.save()
        ha = HitAssignment(
            completed=False,
            expires_at=past,
            hit=hit,
        )
        # Bypass HitAssignment's save(), which updates expires_at
        super(HitAssignment, ha).save()
        self.assertEqual(HitAssignment.objects.count(), 1)

        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.get(reverse('expire_abandoned_assignments'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/admin/turkle')
        self.assertEqual(HitAssignment.objects.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u'All 1 abandoned Tasks have been expired')


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
        project_protected = Project(
            active=True,
            login_required=True,
            name='MY_TEMPLATE_NAME',
        )
        project_protected.save()
        batch = Batch(project=project_protected, name='MY_BATCH_NAME')
        batch.save()
        Hit(batch=batch).save()

        anon_client = django.test.Client()
        response = anon_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'No Tasks available' in response.content)
        self.assertFalse(b'MY_TEMPLATE_NAME' in response.content)
        self.assertFalse(b'MY_BATCH_NAME' in response.content)

        known_client = django.test.Client()
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        known_client.login(username='admin', password='secret')
        response = known_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'No Tasks available' in response.content)
        self.assertTrue(b'MY_TEMPLATE_NAME' in response.content)
        self.assertTrue(b'MY_BATCH_NAME' in response.content)

    def test_index_unprotected_template(self):
        project_unprotected = Project(
            active=True,
            login_required=False,
            name='MY_TEMPLATE_NAME',
        )
        project_unprotected.save()
        batch = Batch(project=project_unprotected, name='MY_BATCH_NAME')
        batch.save()
        Hit(batch=batch).save()

        anon_client = django.test.Client()
        response = anon_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'No Tasks available' in response.content)
        self.assertTrue(b'MY_TEMPLATE_NAME' in response.content)
        self.assertTrue(b'MY_BATCH_NAME' in response.content)

        known_client = django.test.Client()
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        known_client.login(username='admin', password='secret')
        response = known_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'No Tasks available' in response.content)
        self.assertTrue(b'MY_TEMPLATE_NAME' in response.content)
        self.assertTrue(b'MY_BATCH_NAME' in response.content)


class TestIndexAbandonedAssignments(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', password='secret')

        project = Project()
        project.save()
        batch = Batch(project=project)
        batch.save()
        self.hit = Hit(batch=batch)
        self.hit.save()

    def test_index_abandoned_assignment(self):
        HitAssignment(
            assigned_to=self.user,
            completed=False,
            hit=self.hit,
        ).save()

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'You have abandoned' in response.content)

    def test_index_no_abandoned_assignments(self):
        HitAssignment(
            assigned_to=None,
            completed=False,
            hit=self.hit,
        ).save()

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'You have abandoned' in response.content)


class TestHitAssignment(TestCase):
    def setUp(self):
        project = Project(login_required=False, name='foo', html_template='<p></p>')
        project.save()
        batch = Batch(project=project)
        batch.save()
        self.hit = Hit(batch=batch, input_csv_fields='{}')
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
                         u'Cannot find Task with ID {}'.format(666))

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
                         u'Cannot find Task Assignment with ID {}'.format(666))

    def test_get_hit_assignment_with_wrong_user(self):
        user = User.objects.create_user('testuser', password='secret')
        User.objects.create_user('wrong_user', password='secret')
        self.hit_assignment.assigned_to = user
        self.hit_assignment.save()

        client = django.test.Client()
        client.login(username='wrong_user', password='secret')
        response = client.get(reverse('hit_assignment',
                                      kwargs={'hit_id': self.hit.id,
                                              'hit_assignment_id': self.hit_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertTrue(u'You do not have permission to work on the Task Assignment with ID'
                        in str(messages[0]))

    def test_get_hit_assignment_owned_by_user_as_anonymous(self):
        user = User.objects.create_user('testuser', password='secret')
        self.hit_assignment.assigned_to = user
        self.hit_assignment.save()

        client = django.test.Client()
        response = client.get(reverse('hit_assignment',
                                      kwargs={'hit_id': self.hit.id,
                                              'hit_assignment_id': self.hit_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertTrue(u'You do not have permission to work on the Task Assignment with ID'
                        in str(messages[0]))

    def test_submit_assignment_without_auto_accept(self):
        client = django.test.Client()

        s = client.session
        s.update({'auto_accept_status': False})
        s.save()

        response = client.post(reverse('hit_assignment',
                                       kwargs={'hit_id': self.hit.id,
                                               'hit_assignment_id': self.hit_assignment.id}),
                               {u'foo': u'bar'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))

    def test_submit_assignment_with_auto_accept(self):
        client = django.test.Client()

        s = client.session
        s.update({'auto_accept_status': True})
        s.save()

        response = client.post(reverse('hit_assignment',
                                       kwargs={'hit_id': self.hit.id,
                                               'hit_assignment_id': self.hit_assignment.id}),
                               {u'foo': u'bar'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accept_next_hit',
                                                       kwargs={'batch_id': self.hit.batch_id}))


class TestHitAssignmentIFrame(TestCase):
    def setUp(self):
        self.project = Project(login_required=False)
        self.project.save()
        batch = Batch(project=self.project)
        batch.save()
        self.hit = Hit(input_csv_fields={}, batch=batch)
        self.hit.save()
        self.hit_assignment = HitAssignment(hit=self.hit)
        self.hit_assignment.save()

    def test_get_hit_assignment_iframe_with_wrong_user(self):
        user = User.objects.create_user('testuser', password='secret')
        User.objects.create_user('wrong_user', password='secret')
        self.hit_assignment.assigned_to = user
        self.hit_assignment.save()

        client = django.test.Client()
        client.login(username='wrong_user', password='secret')
        response = client.get(reverse('hit_assignment_iframe',
                                      kwargs={'hit_id': self.hit.id,
                                              'hit_assignment_id': self.hit_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertTrue(u'You do not have permission to work on the Task Assignment with ID'
                        in str(messages[0]))

    def test_template_with_submit_button(self):
        self.project.html_template = \
            '<input id="my_submit_button" type="submit" value="MySubmit" />'
        self.project.save()
        self.project.refresh_from_db()
        self.assertTrue(self.project.html_template_has_submit_button)

        client = django.test.Client()
        response = client.get(reverse('hit_assignment_iframe',
                                      kwargs={'hit_id': self.hit.id,
                                              'hit_assignment_id': self.hit_assignment.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'my_submit_button' in response.content)
        self.assertFalse(b'submitButton' in response.content)

    def test_template_without_submit_button(self):
        self.project.form = '<input id="foo" type="text" value="MyText" />'
        self.project.save()
        self.project.refresh_from_db()
        self.assertFalse(self.project.html_template_has_submit_button)

        client = django.test.Client()
        response = client.get(reverse('hit_assignment_iframe',
                                      kwargs={'hit_id': self.hit.id,
                                              'hit_assignment_id': self.hit_assignment.id}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'my_submit_button' in response.content)
        self.assertTrue(b'submitButton' in response.content)


class TestPreview(TestCase):
    def setUp(self):
        self.project = Project(html_template='<p>${foo}: ${bar}</p>',
                               login_required=False, name='foo')
        self.project.save()
        self.batch = Batch(filename='foo.csv', project=self.project, name='foo')
        self.batch.save()
        self.hit = Hit(
            batch=self.batch,
            input_csv_fields={'foo': 'fufu', 'bar': 'baba'},
        )
        self.hit.save()

    def test_get_preview(self):
        client = django.test.Client()
        response = client.get(reverse('preview', kwargs={'hit_id': self.hit.id}))
        self.assertEqual(response.status_code, 200)

    def test_get_preview_as_anonymous_but_login_required(self):
        self.project.login_required = True
        self.project.save()

        client = django.test.Client()
        response = client.get(reverse('preview', kwargs={'hit_id': self.hit.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), u'You do not have permission to view this Task')

    def test_get_preview_bad_hit_id(self):
        client = django.test.Client()
        response = client.get(reverse('preview', kwargs={'hit_id': 666}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u'Cannot find Task with ID {}'.format(666))

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
                         u'Cannot find Task with ID {}'.format(666))

    def test_get_preview_iframe_as_anonymous_but_login_required(self):
        self.project.login_required = True
        self.project.save()

        client = django.test.Client()

        response = client.get(reverse('preview_iframe', kwargs={'hit_id': self.hit.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), u'You do not have permission to view this Task')

    def test_preview_next_hit(self):
        client = django.test.Client()
        response = client.get(reverse('preview_next_hit', kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview', kwargs={'hit_id': self.hit.id}))

    def test_preview_next_hit_no_more_hits(self):
        self.hit.completed = True
        self.hit.save()
        client = django.test.Client()
        response = client.get(reverse('preview_next_hit', kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertTrue(u'No more Tasks are available for Batch' in str(messages[0]))


class TestReturnHitAssignment(TestCase):
    def setUp(self):
        project = Project(name='foo', html_template='<p>${foo}: ${bar}</p>')
        project.save()

        batch = Batch(project=project, name='foo', filename='foo.csv')
        batch.save()

        self.hit = Hit(batch=batch)
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
                         u"The Task can't be returned because it has been completed")

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
                         u'The Task you are trying to return belongs to another user')

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
                         u'The Task you are trying to return belongs to another user')


class TestSkipHit(TestCase):
    def setUp(self):
        project = Project(login_required=False)
        project.save()
        self.batch = Batch(project=project)
        self.batch.save()
        self.hit_one = Hit(batch=self.batch)
        self.hit_one.save()
        self.hit_two = Hit(batch=self.batch)
        self.hit_two.save()
        self.hit_three = Hit(batch=self.batch)
        self.hit_three.save()

    def test_preview_next_hit_order(self):
        client = django.test.Client()

        response = client.get(reverse('preview_next_hit', kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'hit_id': self.hit_one.id}))

        # Since no Tasks have been completed or skipped, preview_next_hit redirects to same Task
        response = client.get(reverse('preview_next_hit', kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'hit_id': self.hit_one.id}))

    def test_skip_hit(self):
        client = django.test.Client()

        # Skip hit_one
        response = client.post(reverse('skip_hit', kwargs={'batch_id': self.batch.id,
                                                           'hit_id': self.hit_one.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview_next_hit',
                                                       kwargs={'batch_id': self.batch.id}))

        # Verify that hit_one has been skipped
        response = client.get(reverse('preview_next_hit',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'hit_id': self.hit_two.id}))

        # Skip hit_two
        response = client.post(reverse('skip_hit', kwargs={'batch_id': self.batch.id,
                                                           'hit_id': self.hit_two.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview_next_hit',
                                                       kwargs={'batch_id': self.batch.id}))

        # Verify that hit_two has been skipped
        response = client.get(reverse('preview_next_hit',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'hit_id': self.hit_three.id}))

        # Skip hit_three
        response = client.post(reverse('skip_hit', kwargs={'batch_id': self.batch.id,
                                                           'hit_id': self.hit_three.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview_next_hit',
                                                       kwargs={'batch_id': self.batch.id}))

        # Verify that, with all existing Tasks skipped, we have been redirected back to
        # hit_one and that info message is displayed about only skipped Tasks remaining
        response = client.get(reverse('preview_next_hit',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'hit_id': self.hit_one.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), u'Only previously skipped Tasks are available')

    def test_skip_and_accept_next_hit(self):
        client = django.test.Client()

        ha_one = HitAssignment(hit=self.hit_one)
        ha_one.save()

        # Skip hit_one
        response = client.post(reverse('skip_and_accept_next_hit',
                                       kwargs={'batch_id': self.batch.id,
                                               'hit_id': self.hit_one.id,
                                               'hit_assignment_id': ha_one.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accept_next_hit',
                                                       kwargs={'batch_id': self.batch.id}))

        # Verify that hit_one has been skipped
        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('{}/assignment/'.format(self.hit_two.id) in response['Location'])

        # Skip hit_two
        ha_two = self.hit_two.hitassignment_set.first()
        response = client.post(reverse('skip_and_accept_next_hit',
                                       kwargs={'batch_id': self.batch.id,
                                               'hit_id': self.hit_two.id,
                                               'hit_assignment_id': ha_two.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accept_next_hit',
                                                       kwargs={'batch_id': self.batch.id}))

        # Verify that hit_two has been skipped
        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('{}/assignment/'.format(self.hit_three.id) in response['Location'])

        # Skip hit_three
        ha_three = self.hit_three.hitassignment_set.first()
        response = client.post(reverse('skip_and_accept_next_hit',
                                       kwargs={'batch_id': self.batch.id,
                                               'hit_id': self.hit_three.id,
                                               'hit_assignment_id': ha_three.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accept_next_hit',
                                                       kwargs={'batch_id': self.batch.id}))

        # Verify that, with all existing Tasks skipped, we have been redirected back to
        # hit_one and that info message is displayed about only skipped Tasks remaining
        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('{}/assignment/'.format(self.hit_one.id) in response['Location'])
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), u'Only previously skipped Tasks are available')

        # Skip hit_one for a second time
        ha_one = self.hit_one.hitassignment_set.first()
        response = client.post(reverse('skip_and_accept_next_hit',
                                       kwargs={'batch_id': self.batch.id,
                                               'hit_id': self.hit_one.id,
                                               'hit_assignment_id': ha_one.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accept_next_hit',
                                                       kwargs={'batch_id': self.batch.id}))

        # Verify that hit_one has been skipped for a second time
        response = client.get(reverse('accept_next_hit',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('{}/assignment/'.format(self.hit_two.id) in response['Location'])
