# -*- coding: utf-8 -*-
import datetime
import os.path

import django.test
from django.contrib.auth.models import Group, User
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone

from turkle.models import Batch, Project, Task, TaskAssignment


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
        task = Task(batch=batch)
        task.save()
        ha = TaskAssignment(
            completed=False,
            expires_at=past,
            task=task,
        )
        # Bypass TaskAssignment's save(), which updates expires_at
        super(TaskAssignment, ha).save()
        self.assertEqual(TaskAssignment.objects.count(), 1)

        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.get(reverse('turkle_admin:expire_abandoned_assignments'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/admin/')
        self.assertEqual(TaskAssignment.objects.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u'All 1 abandoned Tasks have been expired')


class TestBatchAdmin(django.test.TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')

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
                    'assignments_per_task': 1,
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
        self.assertEqual(matching_batch.total_tasks(), 1)
        self.assertEqual(matching_batch.allotted_assignment_time,
                         Batch._meta.get_field('allotted_assignment_time').get_default())
        self.assertEqual(matching_batch.created_by, self.user)

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
                    'assignments_per_task': 1,
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

        self.assertEqual(matching_batch.total_tasks(), 3)
        tasks = matching_batch.task_set.all()
        self.assertEqual(tasks[0].input_csv_fields['emoji'], u'😀')
        self.assertEqual(tasks[0].input_csv_fields['more_emoji'], u'😃')
        self.assertEqual(tasks[2].input_csv_fields['emoji'], u'🤔')
        self.assertEqual(tasks[2].input_csv_fields['more_emoji'], u'🤭')

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
                    'assignments_per_task': 1,
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
                    'assignments_per_task': 1,
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
                'assignments_per_task': 1,
                'project': project.id,
                'name': 'batch_save',
            })
        self.assertTrue(b'error' in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'This field is required' in response.content)

    def test_batch_add_validation_extra_csv_fields(self):
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
                    'assignments_per_task': 1,
                    'project': project.id,
                    'name': 'batch_save',
                    'csv_file': fp
                })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Batch.objects.filter(name='batch_save').exists())
        matching_batch = Batch.objects.filter(name='batch_save').first()
        self.assertEqual(response['Location'], reverse('turkle_admin:review_batch',
                                                       kwargs={'batch_id': matching_batch.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertTrue(u'The CSV file contained fields that are not in the HTML template.'
                        in str(messages[0]))

    def test_batch_add_validation_missing_csv_fields(self):
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
                'assignments_per_task': 1,
                'project': batch.project.id,
                'name': 'batch_save_modified',
            })
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/turkle/batch/')
        self.assertFalse(Batch.objects.filter(name='batch_save').exists())
        self.assertTrue(Batch.objects.filter(name='batch_save_modified').exists())


class TestGroupAdmin(django.test.TestCase):
    def setUp(self):
        User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')

    def test_get_group_add(self):
        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.get(reverse('turkle_admin:auth_group_add'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'error' in response.content)

    def test_post_group_add(self):
        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:auth_group_add'), {
            'name': 'testgroup',
        })
        self.assertFalse(b'error' in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('turkle_admin:auth_group_changelist'))

    def test_post_group_add_add_users(self):
        user_to_add = User.objects.create_user('user_to_add', password='secret')

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:auth_group_add'), {
            'name': 'testgroup',
            'users': [user_to_add.id]
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('turkle_admin:auth_group_changelist'))

        group = Group.objects.get(name='testgroup')
        self.assertEqual(user_to_add, group.user_set.get(id=user_to_add.id))

    def test_get_group_change(self):
        group = Group.objects.create(name='testgroup')
        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.get(reverse('turkle_admin:auth_group_change', args=(group.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'error' in response.content)

    def test_post_group_change(self):
        group = Group.objects.create(name='testgroup')

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:auth_group_change', args=(group.id,)), {
            'name': 'newname',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('turkle_admin:auth_group_changelist'))
        group.refresh_from_db()
        self.assertEqual(group.name, 'newname')

    def test_post_group_change_update_users(self):
        user_to_add = User.objects.create_user('user_to_add', password='secret')
        user_to_remove = User.objects.create_user('user_to_remove', password='secret')
        group = Group.objects.create(name='testgroup')
        group.user_set.add(user_to_remove)

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:auth_group_change', args=(group.id,)), {
            'name': 'newname',
            'users': [user_to_add.id],
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('turkle_admin:auth_group_changelist'))
        group.refresh_from_db()
        self.assertEqual(group.name, 'newname')
        self.assertEqual(1, group.user_set.filter(username='user_to_add').count())
        self.assertEqual(0, group.user_set.filter(username='user_to_remove').count())

    def test_get_group_changelist(self):
        Group.objects.create(name='testgroup')
        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.get(reverse('turkle_admin:auth_group_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'error' in response.content)
        self.assertTrue(b'testgroup' in response.content)


class TestProject(django.test.TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')

    def test_get_add_project(self):
        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.get(reverse('turkle_admin:turkle_project_add'))
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 200)

    def test_post_add_project(self):
        self.assertEqual(Project.objects.filter(name='foo').count(), 0)

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:turkle_project_add'),
                               {
                                   'assignments_per_task': 1,
                                   'name': 'foo',
                                   'html_template': '<p>${foo}: ${bar}</p>',
                               })
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/turkle/project/')
        self.assertEqual(Project.objects.filter(name='foo').count(), 1)
        project = Project.objects.get(name='foo')
        self.assertEqual(project.created_by, self.user)
        self.assertEqual(project.updated_by, self.user)

    def test_get_change_project(self):
        project = Project.objects.create(name='testproject')

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.get(reverse('turkle_admin:turkle_project_change',
                                      args=(project.id,)))
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'testproject' in response.content)

    def test_post_change_project(self):
        project = Project.objects.create(name='testproject')

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:turkle_project_change',
                                       args=(project.id,)),
                               {
                                   'assignments_per_task': 1,
                                   'name': 'newname',
                                   'html_template': '<p>${foo}: ${bar}</p>',
                               })
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/turkle/project/')
        self.assertEqual(Project.objects.filter(name='newname').count(), 1)

    def test_post_change_project_custom_permissions(self):
        project = Project.objects.create(name='testproject')
        user = User.objects.create_user('testuser', password='secret')
        group = Group.objects.create(name='testgroup')
        user.groups.add(group)
        self.assertFalse(user.has_perm('can_work_on', project))

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:turkle_project_change',
                                       args=(project.id,)),
                               {
                                   'assignments_per_task': 1,
                                   'custom_permissions': True,
                                   'html_template': '<p>${foo}: ${bar}</p>',
                                   'name': 'newname',
                                   'worker_permissions': [group.id],
                               })
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/turkle/project/')
        self.assertEqual(Project.objects.filter(name='newname').count(), 1)
        self.assertTrue(user.has_perm('can_work_on', project))

    def test_post_change_project_remove_all_groups(self):
        project = Project.objects.create(name='testproject')
        user = User.objects.create_user('testuser', password='secret')
        group = Group.objects.create(name='testgroup')
        user.groups.add(group)
        group.add_obj_perm('can_work_on', project)
        self.assertTrue(user.has_perm('can_work_on', project))

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:turkle_project_change',
                                       args=(project.id,)),
                               {
                                   'assignments_per_task': 1,
                                   'custom_permissions': True,
                                   'html_template': '<p>${foo}: ${bar}</p>',
                                   'name': 'newname',
                               })
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/turkle/project/')
        self.assertEqual(Project.objects.filter(name='newname').count(), 1)
        self.assertFalse(user.has_perm('can_work_on', project))

    def test_post_change_project_remove_and_add_group(self):
        project = Project.objects.create(name='testproject')
        group_to_add = Group.objects.create(name='group_to_add')
        group_to_remove = Group.objects.create(name='group_to_remove')
        user_for_add = User.objects.create_user('user_for_add', password='secret')
        user_for_remove = User.objects.create_user('user_for_remove', password='secret')
        group_to_remove.add_obj_perm('can_work_on', project)
        user_for_add.groups.add(group_to_add)
        user_for_remove.groups.add(group_to_remove)
        self.assertFalse(user_for_add.has_perm('can_work_on', project))
        self.assertTrue(user_for_remove.has_perm('can_work_on', project))

        client = django.test.Client()
        client.login(username='admin', password='secret')
        response = client.post(reverse('turkle_admin:turkle_project_change',
                                       args=(project.id,)),
                               {
                                   'assignments_per_task': 1,
                                   'custom_permissions': True,
                                   'html_template': '<p>${foo}: ${bar}</p>',
                                   'name': 'newname',
                                   'worker_permissions': [group_to_add.id],
                               })
        self.assertTrue(b'error' not in response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], u'/admin/turkle/project/')
        self.assertEqual(Project.objects.filter(name='newname').count(), 1)
        self.assertTrue(user_for_add.has_perm('can_work_on', project))
        self.assertFalse(user_for_remove.has_perm('can_work_on', project))


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
