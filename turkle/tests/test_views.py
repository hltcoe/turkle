import django.test
from django.contrib.auth.models import Group, User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from guardian.shortcuts import assign_perm
from .utility import save_model

from turkle.models import Task, TaskAssignment, Batch, Project
from turkle.views import parse_date_with_timezone


class TestAcceptTask(TestCase):
    def setUp(self):
        project = Project.objects.create(login_required=False)
        self.batch = Batch.objects.create(login_required=False, project=project)
        self.task = Task.objects.create(batch=self.batch)

    def test_accept_unclaimed_task(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        self.assertEqual(self.task.taskassignment_set.count(), 0)

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.get(reverse('accept_task',
                                      kwargs={'batch_id': self.batch.id,
                                              'task_id': self.task.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.task.taskassignment_set.count(), 1)
        self.assertEqual(response['Location'],
                         reverse('task_assignment',
                                 kwargs={'task_id': self.task.id,
                                         'task_assignment_id':
                                         self.task.taskassignment_set.first().id}))

    def test_accept_unclaimed_task_as_anon(self):
        self.assertEqual(self.task.taskassignment_set.count(), 0)

        client = django.test.Client()
        response = client.get(reverse('accept_task',
                                      kwargs={'batch_id': self.batch.id,
                                              'task_id': self.task.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.task.taskassignment_set.count(), 1)
        self.assertEqual(response['Location'],
                         reverse('task_assignment',
                                 kwargs={'task_id': self.task.id,
                                         'task_assignment_id':
                                         self.task.taskassignment_set.first().id}))

    def test_accept_claimed_task(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        other_user = User.objects.create_user('testuser', password='secret')
        TaskAssignment(assigned_to=other_user, task=self.task).save()
        self.assertEqual(self.task.taskassignment_set.count(), 1)

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.get(reverse('accept_task',
                                      kwargs={'batch_id': self.batch.id,
                                              'task_id': self.task.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         'The Task with ID {} is no longer available'.format(self.task.id))


class TestAcceptNextTask(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            login_required=False,
            html_template='<p>${foo}: ${bar}</p><textarea>',
            name='foo',
        )
        self.batch = Batch.objects.create(
            filename='foo.csv',
            login_required=False,
            name='foo',
            project=self.project,
        )

        self.task = Task.objects.create(
            batch=self.batch,
            input_csv_fields={'foo': 'fufu', 'bar': 'baba'}
        )

    def test_accept_next_task(self):
        user = User.objects.create_user('testuser', password='secret')
        self.assertEqual(self.task.taskassignment_set.count(), 0)

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('accept_next_task',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        # We are redirected to the task_assignment view, but we can't predict the
        # full task_assignment URL
        self.assertTrue('{}/assignment/'.format(self.task.id) in response['Location'])
        self.assertEqual(self.task.taskassignment_set.count(), 1)
        self.assertEqual(self.task.taskassignment_set.first().assigned_to, user)

    def test_accept_next_task_as_anon(self):
        client = django.test.Client()
        response = client.get(reverse('accept_next_task',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        # We are redirected to the task_assignment view, but we can't predict the
        # full task_assignment URL
        self.assertTrue('{}/assignment/'.format(self.task.id) in response['Location'])

    def test_accept_next_task__bad_batch_id(self):
        User.objects.create_user('testuser', password='secret')
        self.assertEqual(self.task.taskassignment_set.count(), 0)

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('accept_next_task',
                                      kwargs={'batch_id': 666}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        self.assertEqual(self.task.taskassignment_set.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         'Cannot find Task Batch with ID {}'.format(666))

    def test_accept_next_task__no_more_tasks(self):
        User.objects.create_user('testuser', password='secret')
        task_assignment = TaskAssignment(completed=True, task=self.task)
        task_assignment.save()
        self.assertEqual(self.task.taskassignment_set.count(), 1)

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('accept_next_task',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        self.assertEqual(self.task.taskassignment_set.count(), 1)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         'No more Tasks available for Batch {}'.format(self.batch.name))

    def test_accept_next_task__respect_skip(self):
        task_two = Task(batch=self.batch)
        task_two.save()

        User.objects.create_user('testuser', password='secret')
        client = django.test.Client()
        client.login(username='testuser', password='secret')

        # Per the Django docs:
        #   To modify the session and then save it, it must be stored in a variable first
        #   (because a new SessionStore is created every time this property is accessed)
        #   https://docs.djangoproject.com/en/3.1/topics/testing/tools/#persistent-state
        s = client.session
        s.update({
            'skipped_tasks_in_batch': {str(self.batch.id): [str(self.task.id)]}
        })
        s.save()

        response = client.get(reverse('accept_next_task',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('{}/assignment/'.format(task_two.id) in response['Location'])

    def test_accept_next_task__deactivated_batch(self):
        self.batch.active = False
        self.batch.save()

        User.objects.create_user('testuser', password='secret')
        self.assertEqual(self.task.taskassignment_set.count(), 0)

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('accept_next_task',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        self.assertEqual(self.task.taskassignment_set.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         'No more Tasks available for Batch {}'.format(self.batch.name))

    def test_accept_next_task__deactivated_project(self):
        self.project.active = False
        self.project.save()

        User.objects.create_user('testuser', password='secret')
        self.assertEqual(self.task.taskassignment_set.count(), 0)

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('accept_next_task',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        self.assertEqual(self.task.taskassignment_set.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         'No more Tasks available for Batch {}'.format(self.batch.name))


class TestDownloadBatchCSV(TestCase):
    def setUp(self):
        project = Project(name='foo', html_template='<p>${foo}: ${bar}</p><textarea>')
        project.save()

        self.batch = Batch(project=project, name='foo', filename='foo.csv')
        self.batch.save()

        task = Task(
            batch=self.batch,
            input_csv_fields={'foo': 'fufu', 'bar': 'baba'}
        )
        task.save()
        TaskAssignment(
            answers={'a1': 'sauce'},
            assigned_to=None,
            completed=True,
            task=task
        ).save()

    def test_get_as_admin(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')

        client = django.test.Client()
        client.login(username='admin', password='secret')
        download_url = reverse('admin:turkle_download_batch', kwargs={'batch_id': self.batch.id})
        response = client.get(download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'),
                         'attachment; filename="%s"' % self.batch.csv_results_filename())

    def test_get_as_rando(self):
        client = django.test.Client()
        client.login(username='not_admin', password='secret')
        download_url = reverse('admin:turkle_download_batch', kwargs={'batch_id': self.batch.id})
        response = client.get(download_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/admin/login/?next=%s' % download_url)


class TestIndex(django.test.TestCase):
    def setUp(self):
        User.objects.create_superuser('ms.admin', 'foo@bar.foo', 'secret')

    def test_get_index(self):
        client = django.test.Client()
        response = client.get('/')
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 200)

    def test_index_login_prompt(self):
        # Display 'Login' link when NOT logged in
        client = django.test.Client()
        response = client.get('/')
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Login' in response.content)

    def test_index_logout_prompt(self):
        # Display 'Logout' link and username when logged in
        client = django.test.Client()
        client.login(username='ms.admin', password='secret')
        response = client.get('/')
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Logout' in response.content)
        self.assertTrue(b'ms.admin' in response.content)

    def test_index_permission_protected_project(self):
        project = Project.objects.create(
            active=True,
            custom_permissions=True,
            login_required=True,
            name='MY_TEMPLATE_NAME',
        )
        batch = Batch.objects.create(
            custom_permissions=True,
            login_required=True,
            name='MY_BATCH_NAME',
            project=project,
        )
        Task.objects.create(batch=batch)

        # Verify that User directly assigned to Batch can access Batch
        user_direct_access = User.objects.create_user('user_direct_access', password='secret')
        assign_perm('can_work_on_batch', user_direct_access, batch)
        direct_access_client = django.test.Client()
        direct_access_client.login(username='user_direct_access', password='secret')
        response = direct_access_client.get(reverse('index'))
        self.assertFalse(b'No Tasks available' in response.content)
        self.assertTrue(b'MY_TEMPLATE_NAME' in response.content)
        self.assertTrue(b'MY_BATCH_NAME' in response.content)

        # Verify that User who is a member of a Group assigned to Batch can access Batch
        user_group_access = User.objects.create_user('user_group_access', password='secret')
        group = Group.objects.create(name='testgroup')
        user_group_access.groups.add(group)
        assign_perm('can_work_on_batch', group, batch)
        group_access_client = django.test.Client()
        group_access_client.login(username='user_group_access', password='secret')
        response = group_access_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'No Tasks available' in response.content)
        self.assertTrue(b'MY_TEMPLATE_NAME' in response.content)
        self.assertTrue(b'MY_BATCH_NAME' in response.content)

        # Verify that User without direct/group assignment to Batch CANNOT access Batch
        User.objects.create_user('out_user', password='secret')
        out_client = django.test.Client()
        out_client.login(username='out_user', password='secret')
        response = out_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'No Tasks available' in response.content)
        self.assertFalse(b'MY_TEMPLATE_NAME' in response.content)
        self.assertFalse(b'MY_BATCH_NAME' in response.content)

    def test_index_protected_project(self):
        project_protected = Project.objects.create(
            active=True,
            login_required=True,
            name='MY_TEMPLATE_NAME',
        )
        batch = Batch.objects.create(
            login_required=True,
            name='MY_BATCH_NAME',
            project=project_protected,
        )
        Task.objects.create(batch=batch)

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
        project_unprotected = Project.objects.create(
            active=True,
            login_required=False,
            name='MY_TEMPLATE_NAME',
        )
        batch = Batch.objects.create(
            login_required=False,
            name='MY_BATCH_NAME',
            project=project_unprotected,
        )
        Task.objects.create(batch=batch)

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

    def test_index_unprotected_template_bad_batch(self):
        project_unprotected = Project.objects.create(
            active=True,
            login_required=False,
            name='MY_TEMPLATE_NAME',
        )
        # In theory, Turkle should prevent the creation of Batches where login_required == False
        # and assignments_per_task != 1
        batch = Batch.objects.create(
            assignments_per_task=2,
            login_required=False,
            name='MY_BATCH_NAME',
            project=project_unprotected,
        )
        Task.objects.create(batch=batch)

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


class TestIndexAbandonedAssignments(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', password='secret')

        self.project = Project()
        self.project.save()
        self.batch = Batch(project=self.project)
        self.batch.save()
        self.task = Task(batch=self.batch)
        self.task.save()

    def test_index_abandoned_assignment(self):
        TaskAssignment(
            assigned_to=self.user,
            completed=False,
            task=self.task,
        ).save()

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'You have abandoned' in response.content)

    def test_index_abandoned_assignment_from_inactive_batch(self):
        # Don't show abandoned tasks from inactive batches
        TaskAssignment(
            assigned_to=self.user,
            completed=False,
            task=self.task,
        ).save()

        self.project.active = False
        self.project.save()

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'You have abandoned' in response.content)

    def test_index_abandoned_assignment_from_inactive_project(self):
        # Don't show abandoned tasks from inactive projects
        TaskAssignment(
            assigned_to=self.user,
            completed=False,
            task=self.task,
        ).save()

        self.batch.active = False
        self.batch.save()

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'You have abandoned' in response.content)

    def test_index_no_abandoned_assignments(self):
        TaskAssignment(
            assigned_to=None,
            completed=False,
            task=self.task,
        ).save()

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'You have abandoned' in response.content)


class TestTaskAssignment(TestCase):
    def setUp(self):
        project = Project(login_required=False, name='foo', html_template='<p></p><textarea>')
        project.save()
        batch = Batch(project=project)
        batch.save()
        self.task = Task(batch=batch, input_csv_fields='{}')
        self.task.save()
        self.task_assignment = TaskAssignment(
            assigned_to=None,
            completed=False,
            task=self.task
        )
        self.task_assignment.save()

    def test_get_task_assignment(self):
        client = django.test.Client()
        response = client.get(reverse('task_assignment',
                                      kwargs={'task_id': self.task.id,
                                              'task_assignment_id': self.task_assignment.id}))
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 0)

    def test_get_task_assignment_with_bad_task_id(self):
        client = django.test.Client()
        response = client.get(reverse('task_assignment',
                                      kwargs={'task_id': 666,
                                              'task_assignment_id': self.task_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         'Cannot find Task with ID {}'.format(666))

    def test_get_task_assignment_with_bad_task_assignment_id(self):
        client = django.test.Client()
        response = client.get(reverse('task_assignment',
                                      kwargs={'task_id': self.task.id,
                                              'task_assignment_id': 666}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         'Cannot find Task Assignment with ID {}'.format(666))

    def test_get_task_assignment_with_wrong_user(self):
        user = User.objects.create_user('testuser', password='secret')
        User.objects.create_user('wrong_user', password='secret')
        self.task_assignment.assigned_to = user
        self.task_assignment.save()

        client = django.test.Client()
        client.login(username='wrong_user', password='secret')
        response = client.get(reverse('task_assignment',
                                      kwargs={'task_id': self.task.id,
                                              'task_assignment_id': self.task_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertTrue('You do not have permission to work on the Task Assignment with ID'
                        in str(messages[0]))

    def test_get_task_assignment_owned_by_user_as_anonymous(self):
        user = User.objects.create_user('testuser', password='secret')
        self.task_assignment.assigned_to = user
        self.task_assignment.save()

        client = django.test.Client()
        response = client.get(reverse('task_assignment',
                                      kwargs={'task_id': self.task.id,
                                              'task_assignment_id': self.task_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertTrue('You do not have permission to work on the Task Assignment with ID'
                        in str(messages[0]))

    def test_submit_assignment_without_auto_accept(self):
        client = django.test.Client()

        s = client.session
        s.update({'auto_accept_status': False})
        s.save()

        response = client.post(reverse('task_assignment',
                                       kwargs={'task_id': self.task.id,
                                               'task_assignment_id': self.task_assignment.id}),
                               {'foo': 'bar'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))

    def test_submit_assignment_with_auto_accept(self):
        client = django.test.Client()

        s = client.session
        s.update({'auto_accept_status': True})
        s.save()

        response = client.post(reverse('task_assignment',
                                       kwargs={'task_id': self.task.id,
                                               'task_assignment_id': self.task_assignment.id}),
                               {'foo': 'bar'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accept_next_task',
                                                       kwargs={'batch_id': self.task.batch_id}))


class TestTaskAssignmentIFrame(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', password='secret')
        self.admin = User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        self.project = Project(name="Test", login_required=False)
        self.project.created_by = self.admin
        self.project.updated_by = self.admin
        self.project.save()
        batch = Batch(project=self.project)
        batch.save()
        self.task = Task(input_csv_fields={}, batch=batch)
        self.task.save()
        self.task_assignment = TaskAssignment(task=self.task)
        self.task_assignment.save()

    def test_get_task_assignment_iframe_with_wrong_user(self):
        User.objects.create_user('wrong_user', password='secret')
        self.task_assignment.assigned_to = self.user
        self.task_assignment.save()

        client = django.test.Client()
        client.login(username='wrong_user', password='secret')
        response = client.get(reverse('task_assignment_iframe',
                                      kwargs={'task_id': self.task.id,
                                              'task_assignment_id': self.task_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertTrue('You do not have permission to work on the Task Assignment with ID'
                        in str(messages[0]))

    def test_template_with_submit_button(self):
        self.project.html_template = \
            '<input id="my_submit_button" type="submit" value="MySubmit" />'
        save_model(self.project)
        self.project.refresh_from_db()
        self.assertTrue(self.project.html_template_has_submit_button)

        client = django.test.Client()
        response = client.get(reverse('task_assignment_iframe',
                                      kwargs={'task_id': self.task.id,
                                              'task_assignment_id': self.task_assignment.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'my_submit_button' in response.content)
        self.assertFalse(b'submitButton' in response.content)

    def test_template_without_submit_button(self):
        self.project.form = '<input id="foo" type="text" value="MyText" />'
        self.project.save()
        self.project.refresh_from_db()
        self.assertFalse(self.project.html_template_has_submit_button)

        client = django.test.Client()
        response = client.get(reverse('task_assignment_iframe',
                                      kwargs={'task_id': self.task.id,
                                              'task_assignment_id': self.task_assignment.id}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'my_submit_button' in response.content)
        self.assertTrue(b'submitButton' in response.content)


class TestPreview(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            html_template='<p>${foo}: ${bar}</p><textarea>',
            login_required=False,
            name='foo'
        )
        self.batch = Batch.objects.create(
            filename='foo.csv',
            login_required=False,
            name='foo',
            project=self.project,
        )
        self.task = Task.objects.create(
            batch=self.batch,
            input_csv_fields={'foo': 'fufu', 'bar': 'baba'},
        )

    def test_get_preview(self):
        client = django.test.Client()
        response = client.get(reverse('preview', kwargs={'task_id': self.task.id}))
        self.assertEqual(response.status_code, 200)

    def test_get_preview_as_anonymous_but_login_required(self):
        self.project.login_required = True
        self.project.save()

        client = django.test.Client()
        response = client.get(reverse('preview', kwargs={'task_id': self.task.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'You do not have permission to view this Task')

    def test_get_preview_bad_task_id(self):
        client = django.test.Client()
        response = client.get(reverse('preview', kwargs={'task_id': 666}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         'Cannot find Task with ID {}'.format(666))

    def test_get_preview_iframe(self):
        client = django.test.Client()
        response = client.get(reverse('preview_iframe', kwargs={'task_id': self.task.id}))
        self.assertEqual(response.status_code, 200)

    def test_get_preview_iframe_bad_task_id(self):
        client = django.test.Client()
        response = client.get(reverse('preview_iframe', kwargs={'task_id': 666}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         'Cannot find Task with ID {}'.format(666))

    def test_get_preview_iframe_as_anonymous_but_login_required(self):
        self.project.login_required = True
        self.project.save()

        client = django.test.Client()

        response = client.get(reverse('preview_iframe', kwargs={'task_id': self.task.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'You do not have permission to view this Task')

    def test_preview_next_task(self):
        client = django.test.Client()
        response = client.get(reverse('preview_next_task', kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'task_id': self.task.id}))

    def test_preview_next_task_no_more_tasks(self):
        self.task.completed = True
        self.task.save()
        client = django.test.Client()
        response = client.get(reverse('preview_next_task', kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertTrue('No more Tasks are available for Batch' in str(messages[0]))


class TestReturnTaskAssignment(TestCase):
    def setUp(self):
        project = Project(name='foo', html_template='<p>${foo}: ${bar}</p><textarea>')
        project.save()

        batch = Batch(project=project, name='foo', filename='foo.csv')
        batch.save()

        self.task = Task(batch=batch)
        self.task.save()

    def test_return_task_assignment(self):
        user = User.objects.create_user('testuser', password='secret')

        task_assignment = TaskAssignment(
            assigned_to=user,
            task=self.task
        )
        task_assignment.save()

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('return_task_assignment',
                                      kwargs={'task_id': self.task.id,
                                              'task_assignment_id': task_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))

    def test_return_completed_task_assignment(self):
        user = User.objects.create_user('testuser', password='secret')

        task_assignment = TaskAssignment(
            assigned_to=user,
            completed=True,
            task=self.task
        )
        task_assignment.save()

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('return_task_assignment',
                                      kwargs={'task_id': self.task.id,
                                              'task_assignment_id': task_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         "The Task can't be returned because it has been completed")

    def test_return_task_assignment_as_anonymous_user(self):
        task_assignment = TaskAssignment(
            assigned_to=None,
            task=self.task
        )
        task_assignment.save()

        client = django.test.Client()
        response = client.get(reverse('return_task_assignment',
                                      kwargs={'task_id': self.task.id,
                                              'task_assignment_id': task_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))

    def test_return_task_assignment__anon_user_returns_other_users_task(self):
        user = User.objects.create_user('testuser', password='secret')

        task_assignment = TaskAssignment(
            assigned_to=user,
            task=self.task
        )
        task_assignment.save()

        client = django.test.Client()
        response = client.get(reverse('return_task_assignment',
                                      kwargs={'task_id': self.task.id,
                                              'task_assignment_id': task_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         'The Task you are trying to return belongs to another user')

    def test_return_task_assignment__user_returns_anon_users_task(self):
        User.objects.create_user('testuser', password='secret')

        task_assignment = TaskAssignment(
            assigned_to=None,
            task=self.task
        )
        task_assignment.save()

        client = django.test.Client()
        client.login(username='testuser', password='secret')
        response = client.get(reverse('return_task_assignment',
                                      kwargs={'task_id': self.task.id,
                                              'task_assignment_id': task_assignment.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         'The Task you are trying to return belongs to another user')


class TestSkipTask(TestCase):
    def setUp(self):
        project = Project.objects.create(login_required=False)
        self.batch = Batch.objects.create(login_required=False, project=project)
        self.task_one = Task.objects.create(batch=self.batch)
        self.task_two = Task.objects.create(batch=self.batch)
        self.task_three = Task.objects.create(batch=self.batch)

    def test_preview_next_task_order(self):
        client = django.test.Client()

        response = client.get(reverse('preview_next_task', kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'task_id': self.task_one.id}))

        # Since no Tasks have been completed or skipped, preview_next_task redirects to same Task
        response = client.get(reverse('preview_next_task', kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'task_id': self.task_one.id}))

    def test_skip_task(self):
        client = django.test.Client()

        # Skip task_one
        response = client.post(reverse('skip_task', kwargs={'batch_id': self.batch.id,
                                                            'task_id': self.task_one.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview_next_task',
                                                       kwargs={'batch_id': self.batch.id}))

        # Verify that task_one has been skipped
        response = client.get(reverse('preview_next_task',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'task_id': self.task_two.id}))

        # Skip task_two
        response = client.post(reverse('skip_task', kwargs={'batch_id': self.batch.id,
                                                            'task_id': self.task_two.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview_next_task',
                                                       kwargs={'batch_id': self.batch.id}))

        # Verify that task_two has been skipped
        response = client.get(reverse('preview_next_task',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'task_id': self.task_three.id}))

        # Skip task_three
        response = client.post(reverse('skip_task', kwargs={'batch_id': self.batch.id,
                                                            'task_id': self.task_three.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview_next_task',
                                                       kwargs={'batch_id': self.batch.id}))

        # Verify that, with all existing Tasks skipped, we have been redirected back to
        # task_one and that info message is displayed about only skipped Tasks remaining
        response = client.get(reverse('preview_next_task',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('preview',
                                                       kwargs={'task_id': self.task_one.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Only previously skipped Tasks are available')

    def test_skip_and_accept_next_task(self):
        client = django.test.Client()

        ha_one = TaskAssignment(task=self.task_one)
        ha_one.save()

        # Skip task_one
        response = client.post(reverse('skip_and_accept_next_task',
                                       kwargs={'batch_id': self.batch.id,
                                               'task_id': self.task_one.id,
                                               'task_assignment_id': ha_one.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accept_next_task',
                                                       kwargs={'batch_id': self.batch.id}))

        # Verify that task_one has been skipped
        response = client.get(reverse('accept_next_task',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('{}/assignment/'.format(self.task_two.id) in response['Location'])

        # Skip task_two
        ha_two = self.task_two.taskassignment_set.first()
        response = client.post(reverse('skip_and_accept_next_task',
                                       kwargs={'batch_id': self.batch.id,
                                               'task_id': self.task_two.id,
                                               'task_assignment_id': ha_two.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accept_next_task',
                                                       kwargs={'batch_id': self.batch.id}))

        # Verify that task_two has been skipped
        response = client.get(reverse('accept_next_task',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('{}/assignment/'.format(self.task_three.id) in response['Location'])

        # Skip task_three
        ha_three = self.task_three.taskassignment_set.first()
        response = client.post(reverse('skip_and_accept_next_task',
                                       kwargs={'batch_id': self.batch.id,
                                               'task_id': self.task_three.id,
                                               'task_assignment_id': ha_three.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accept_next_task',
                                                       kwargs={'batch_id': self.batch.id}))

        # Verify that, with all existing Tasks skipped, we have been redirected back to
        # task_one and that info message is displayed about only skipped Tasks remaining
        response = client.get(reverse('accept_next_task',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('{}/assignment/'.format(self.task_one.id) in response['Location'])
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Only previously skipped Tasks are available')

        # Skip task_one for a second time
        ha_one = self.task_one.taskassignment_set.first()
        response = client.post(reverse('skip_and_accept_next_task',
                                       kwargs={'batch_id': self.batch.id,
                                               'task_id': self.task_one.id,
                                               'task_assignment_id': ha_one.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accept_next_task',
                                                       kwargs={'batch_id': self.batch.id}))

        # Verify that task_one has been skipped for a second time
        response = client.get(reverse('accept_next_task',
                                      kwargs={'batch_id': self.batch.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('{}/assignment/'.format(self.task_two.id) in response['Location'])


class TestStats(django.test.TestCase):
    def setUp(self):
        self.user = User.objects.create_user('mr.user', 'foo@bar.foo', 'secret')
        self.staff = User.objects.create_user('ms.staff', 'foo@bar.foo', 'secret', is_staff=True)

    def test_parse_date_with_timezone_with_valid_string(self):
        dt = parse_date_with_timezone("2022-04-01")
        self.assertEqual(dt.year, 2022)
        self.assertEqual(dt.month, 4)
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.hour, 0)
        self.assertIsNotNone(dt.tzinfo)

    def test_stats_self(self):
        client = django.test.Client()
        client.login(username='mr.user', password='secret')
        response = client.get(reverse('stats'))
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 200)

    def test_stats_for_user_self_as_user(self):
        client = django.test.Client()
        client.login(username='mr.user', password='secret')
        response = client.get(reverse('stats_for_user', kwargs={'user_id': self.user.id}))
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 200)

    def test_stats_for_user_other_as_not_staff(self):
        client = django.test.Client()
        client.login(username='mr.user', password='secret')
        response = client.get(reverse('stats_for_user', kwargs={'user_id': self.staff.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u"You cannot view another User's statistics unless you are Staff")

    def test_stats_for_user_other_as_staff(self):
        client = django.test.Client()
        client.login(username='ms.staff', password='secret')
        response = client.get(reverse('stats_for_user', kwargs={'user_id': self.user.id}))
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 200)
