import datetime
from io import StringIO
import os.path
import time
from unittest import mock

from django.contrib.auth.models import AnonymousUser, Group, User
from django.core.exceptions import ValidationError
import django.test
from django.utils import timezone
from guardian.shortcuts import assign_perm, get_group_perms

from .utility import save_model
from turkle.models import Task, TaskAssignment, Batch, Project, ActiveProject, ActiveProjectManager
from turkle.utils import get_turkle_template_limit


class TestBatch(django.test.TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')

    def test_access_permitted_for_active_flag(self):
        user = User.objects.create_user('testuser', password='secret')

        self.assertEqual(len(Batch.access_permitted_for(user)), 0)

        active_project = Project.objects.create()
        inactive_project = Project.objects.create(active=False)

        Batch.objects.create(
            active=False,
            project=active_project,
        )
        self.assertEqual(len(Batch.access_permitted_for(user)), 0)

        Batch.objects.create(
            active=False,
            project=inactive_project
        )
        self.assertEqual(len(Batch.access_permitted_for(user)), 0)

        Batch.objects.create(
            active=True,
            project=inactive_project
        )
        self.assertEqual(len(Batch.access_permitted_for(user)), 0)

        Batch.objects.create(
            active=True,
            project=active_project,
        )
        self.assertEqual(len(Batch.access_permitted_for(user)), 1)

    def test_access_permitted_for_login_required(self):
        anonymous_user = AnonymousUser()

        self.assertEqual(len(Batch.access_permitted_for(anonymous_user)), 0)

        project = Project.objects.create()
        Batch.objects.create(login_required=True, project=project)
        self.assertEqual(len(Batch.access_permitted_for(anonymous_user)), 0)

        authenticated_user = User.objects.create_user('testuser', password='secret')
        self.assertEqual(len(Batch.access_permitted_for(authenticated_user)), 1)

    def test_access_permitted_for_custom_permissions(self):
        user = User.objects.create_user('testuser', password='secret')
        group = Group.objects.create(name='testgroup')
        user.groups.add(group)
        project = Project.objects.create(custom_permissions=True)
        batch = Batch.objects.create(custom_permissions=True, project=project)

        self.assertEqual(len(batch.access_permitted_for(user)), 0)

        # Verify that giving the group access also gives the group members access
        self.assertFalse(user.has_perm('can_work_on_batch', batch))
        assign_perm('can_work_on_batch', group, batch)
        self.assertEqual(len(batch.access_permitted_for(user)), 1)

        # add superusers should have access to it
        self.assertEqual(len(batch.access_permitted_for(self.admin)), 1)

    def test_available_for(self):
        user = User.objects.create_user('testuser', password='secret')
        project = Project.objects.create()
        batch = Batch.objects.create(project=project)

        self.assertTrue(batch.available_for(user))

        batch.active = False
        self.assertFalse(batch.available_for(user))

    def test_available_for_deactivated_project(self):
        user = User.objects.create_user('testuser', password='secret')
        project = Project.objects.create(active=False)
        batch = Batch.objects.create(project=project)

        self.assertFalse(batch.available_for(user))

    def test_available_tasks_for(self):
        user = User.objects.create_user('testuser', password='secret')
        project = Project.objects.create()
        batch = Batch.objects.create(project=project)
        task1 = Task(
            batch=batch,
            completed=False,
            input_csv_fields={'number': '1', 'letter': 'a'},
        )
        task1.save()

        self.assertEqual(1, len(batch.available_tasks_for(user)))

        batch.active = False
        self.assertEqual(0, len(batch.available_tasks_for(user)))

    def test_available_task_for_deactivated_project(self):
        user = User.objects.create_user('testuser', password='secret')
        project = Project.objects.create(active=False)
        batch = Batch.objects.create(project=project)
        task1 = Task(
            batch=batch,
            completed=False,
            input_csv_fields={'number': '1', 'letter': 'a'},
        )
        task1.save()

        self.assertEqual(0, len(batch.available_tasks_for(user)))

    def test_batch_to_csv(self):
        template = '<p>${number} - ${letter}</p><textarea>'
        project = Project.objects.create(name='test', html_template=template)
        batch = Batch.objects.create(project=project)
        user = User.objects.create(username='joe')

        task1 = Task(
            batch=batch,
            completed=True,
            input_csv_fields={'number': '1', 'letter': 'a'},
        )
        task1.save()
        ta = TaskAssignment(
            answers={'combined': '1a'},
            assigned_to=user,
            completed=True,
            task=task1,
        )
        ta.save()
        time_string = ta.created_at.strftime("%a %b %d %H:%M:%S %Z %Y")

        task2 = Task(
            batch=batch,
            completed=True,
            input_csv_fields={'number': '2', 'letter': 'b'},
        )
        task2.save()
        TaskAssignment(
            answers={'combined': '2b'},
            assigned_to=user,
            completed=True,
            task=task2
        ).save()

        csv_output = StringIO()
        batch.to_csv(csv_output)
        csv_string = csv_output.getvalue()
        self.assertTrue(
            '"Input.letter","Input.number","Answer.combined","Turkle.Username"\r\n'
            in csv_string)
        self.assertTrue('"b","2","2b","joe"\r\n' in csv_string)
        self.assertTrue('"a","1","1a","joe"\r\n' in csv_string)
        self.assertTrue(time_string in csv_string)

    def test_batch_to_input_csv(self):
        project = Project(name='test', html_template='<p>${letter}</p><textarea>')
        project.save()
        batch = Batch(project=project)
        batch.save()

        task1 = Task(
            batch=batch,
            completed=True,
            input_csv_fields={'letter': 'a', 'number': '1'},
        )
        task1.save()
        task2 = Task(
            batch=batch,
            completed=True,
            input_csv_fields={'letter': 'b', 'number': '2'},
        )
        task2.save()

        csv_output = StringIO()
        batch.to_input_csv(csv_output)
        rows = csv_output.getvalue().split()

        # Original column order not guaranteed
        if '"letter","number"' in rows[0]:
            self.assertTrue(any(['"a","1"' in row for row in rows[1:]]))
            self.assertTrue(any(['"b","2"' in row for row in rows[1:]]))
        elif '"number","letter"' in rows[0]:
            self.assertTrue(any(['"1","a"' in row for row in rows[1:]]))
            self.assertTrue(any(['"2","b"' in row for row in rows[1:]]))
        else:
            self.fail('Unexpected header value: %s' % rows[0])

    def test_batch_to_csv_variable_number_of_answers(self):
        project = Project(name='test', html_template='<p>${letter}</p><textarea>')
        project.save()
        batch = Batch(project=project)
        batch.save()

        task1 = Task(
            batch=batch,
            completed=True,
            input_csv_fields={'letter': 'a'},
        )
        task1.save()
        TaskAssignment(
            answers={'1': 1, '2': 2},
            assigned_to=None,
            completed=True,
            task=task1,
        ).save()

        task2 = Task(
            batch=batch,
            completed=True,
            input_csv_fields={'letter': 'b'},
        )
        task2.save()
        TaskAssignment(
            answers={'3': 3, '4': 4},
            assigned_to=None,
            completed=True,
            task=task2
        ).save()

        task3 = Task(
            batch=batch,
            completed=True,
            input_csv_fields={'letter': 'c'},
        )
        task3.save()
        TaskAssignment(
            answers={'3': 3, '2': 2},
            assigned_to=None,
            completed=True,
            task=task3
        ).save()

        csv_output = StringIO()
        batch.to_csv(csv_output)
        rows = csv_output.getvalue().split()
        self.assertTrue('"Input.letter","Answer.1","Answer.2","Answer.3","Answer.4"' in rows[0])
        self.assertTrue(any(['"a","1","2","",""' in row for row in rows[1:]]))
        self.assertTrue(any(['"b","","","3","4"' in row for row in rows[1:]]))
        self.assertTrue(any(['"c","","2","3",""' in row for row in rows[1:]]))

    def test_batch_to_csv_partially_completed_task(self):
        project = Project.objects.create(
            name='test', html_template='<p>${number} - ${letter}</p><textarea>')
        batch = Batch.objects.create(
            assignments_per_task=2,
            project=project
        )
        task = Task.objects.create(
            batch=batch,
            input_csv_fields={'number': '1', 'letter': 'a'},
        )

        csv_output = StringIO()
        batch.to_csv(csv_output)
        rows = csv_output.getvalue().splitlines()
        self.assertEqual(len(rows), 1)

        # Task Assignments that have not been completed should not generate CSV lines
        ta = TaskAssignment.objects.create(
            answers={'combined': '1a'},
            task=task,
        )
        csv_output = StringIO()
        batch.to_csv(csv_output)
        rows = csv_output.getvalue().splitlines()
        self.assertEqual(len(rows), 1)

        ta.completed = True
        ta.save()
        csv_output = StringIO()
        batch.to_csv(csv_output)
        rows = csv_output.getvalue().splitlines()
        self.assertEqual(len(rows), 2)

        TaskAssignment.objects.create(
            answers={'combined': '1a'},
            completed=True,
            task=task,
        )
        csv_output = StringIO()
        batch.to_csv(csv_output)
        rows = csv_output.getvalue().splitlines()
        self.assertEqual(len(rows), 3)

    def test_batch_from_emoji_csv(self):
        template = '<p>${emoji} - ${more_emoji}</p><textarea>'
        project = Project(name='test', html_template=template)
        project.save()
        batch = Batch(project=project)
        batch.save()

        with open(os.path.abspath('turkle/tests/resources/emoji.csv'), 'r') as csv_fh:
            batch.create_tasks_from_csv(csv_fh)

        self.assertEqual(batch.total_tasks(), 3)
        tasks = batch.task_set.all()
        self.assertEqual(tasks[0].input_csv_fields['emoji'], '😀')
        self.assertEqual(tasks[0].input_csv_fields['more_emoji'], '😃')
        self.assertEqual(tasks[2].input_csv_fields['emoji'], '🤔')
        self.assertEqual(tasks[2].input_csv_fields['more_emoji'], '🤭')

    def test_copy_project_permissions(self):
        project = Project.objects.create(
            custom_permissions=True,
            login_required=True,
        )
        group = Group.objects.create(name='testgroup')
        assign_perm('can_work_on', group, project)
        batch = Batch.objects.create(
            custom_permissions=False,
            login_required=False,
            project=project,
        )
        self.assertFalse('can_work_on_batch' in get_group_perms(group, batch))

        batch.copy_project_permissions()
        self.assertTrue(batch.custom_permissions)
        self.assertTrue(batch.login_required)
        self.assertTrue('can_work_on_batch' in get_group_perms(group, batch))

    def test_copy_project_permissions_no_custom_permissions(self):
        project = Project.objects.create(
            custom_permissions=False,
            login_required=False,
        )
        group = Group.objects.create(name='testgroup')
        assign_perm('can_work_on', group, project)
        batch = Batch.objects.create(
            custom_permissions=True,
            login_required=True,
            project=project,
        )
        self.assertFalse('can_work_on_batch' in get_group_perms(group, batch))

        batch.copy_project_permissions()
        self.assertFalse(batch.custom_permissions)
        self.assertFalse(batch.login_required)
        self.assertFalse('can_work_on_batch' in get_group_perms(group, batch))

    def test_login_required_validation_1(self):
        # No ValidationError thrown
        project = Project(
            name='test',
            login_required=False,
            html_template='<textarea>',
            created_by=self.admin,
            updated_by=self.admin,
        )
        save_model(project)
        Batch(
            name='test',
            assignments_per_task=1,
            project=project,
        ).clean()

    def test_login_required_validation_2(self):
        # No ValidationError thrown
        project = Project(
            name='test',
            login_required=True,
            html_template='<textarea>',
            created_by=self.admin,
            updated_by=self.admin,
        )
        save_model(project)
        Batch(
            name='test',
            assignments_per_task=2,
            project=project,
        ).clean()

    def test_login_required_validation_3(self):
        with self.assertRaisesMessage(ValidationError, 'Assignments per Task must be 1'):
            project = Project(
                name='test',
                html_template='<textarea>',
                created_by=self.admin,
                updated_by=self.admin,
            )
            save_model(project)
            Batch(
                name='test',
                assignments_per_task=2,
                login_required=False,
                project=project,
            ).clean()


class TestBatchAvailableTasks(django.test.TestCase):
    def setUp(self):
        self.batch_query = Batch.objects.all()
        self.user = User.objects.create_user('testuser', password='secret')

        template = '<p>${number} - ${letter}</p><textarea>'
        self.project = Project.objects.create(name='test', html_template=template)

    def test_available_tasks_for__apt_is_1(self):
        batch = Batch(
            assignments_per_task=1,
            project=self.project
        )
        batch.save()
        self.assertEqual(batch.total_available_tasks_for(self.user), 0)
        self.assertEqual(Batch.available_task_counts_for(self.batch_query, self.user)[batch.id], 0)
        self.assertEqual(batch.next_available_task_for(self.user), None)

        task = Task(
            batch=batch,
        )
        task.save()
        self.assertEqual(batch.total_available_tasks_for(self.user), 1)
        self.assertEqual(Batch.available_task_counts_for(self.batch_query, self.user)[batch.id], 1)
        self.assertEqual(batch.next_available_task_for(self.user), task)

        task_assignment = TaskAssignment(
            assigned_to=self.user,
            completed=False,
            task=task,
        )
        task_assignment.save()
        self.assertEqual(batch.total_available_tasks_for(self.user), 0)
        self.assertEqual(Batch.available_task_counts_for(self.batch_query, self.user)[batch.id], 0)
        self.assertEqual(batch.next_available_task_for(self.user), None)

    def test_available_tasks_for__apt_is_2(self):
        batch = Batch(
            assignments_per_task=2,
            project=self.project
        )
        batch.save()
        self.assertEqual(batch.total_available_tasks_for(self.user), 0)
        self.assertEqual(Batch.available_task_counts_for(self.batch_query, self.user)[batch.id], 0)

        task = Task(
            batch=batch,
        )
        task.save()
        self.assertEqual(batch.total_available_tasks_for(self.user), 1)
        self.assertEqual(Batch.available_task_counts_for(self.batch_query, self.user)[batch.id], 1)

        task_assignment = TaskAssignment(
            assigned_to=self.user,
            completed=False,
            task=task,
        )
        task_assignment.save()
        self.assertEqual(batch.total_available_tasks_for(self.user), 0)
        self.assertEqual(Batch.available_task_counts_for(self.batch_query, self.user)[batch.id], 0)

        other_user = User.objects.create_user('other_user', password='secret')
        self.assertEqual(batch.total_available_tasks_for(other_user), 1)

        task_assignment = TaskAssignment(
            assigned_to=other_user,
            completed=False,
            task=task,
        )
        task_assignment.save()
        self.assertEqual(batch.total_available_tasks_for(other_user), 0)
        self.assertEqual(Batch.available_task_counts_for(self.batch_query, self.user)[batch.id], 0)

    def test_available_tasks_for_anon_user(self):
        anon_user = AnonymousUser()
        user = User.objects.create_user('user', password='secret')

        self.assertEqual(len(Batch.access_permitted_for(user)), 0)
        batch_protected = Batch.objects.create(
            active=True,
            login_required=True,
            project=self.project
        )
        self.assertEqual(len(Batch.access_permitted_for(anon_user)), 0)
        self.assertEqual(len(Batch.access_permitted_for(user)), 1)

        Task.objects.create(batch=batch_protected)
        self.assertEqual(len(batch_protected.available_tasks_for(anon_user)), 0)
        self.assertEqual(
            Batch.available_task_counts_for(self.batch_query, anon_user)[batch_protected.id], 0)
        self.assertEqual(len(batch_protected.available_tasks_for(user)), 1)
        self.assertEqual(
            Batch.available_task_counts_for(self.batch_query, user)[batch_protected.id], 1)

        batch_unprotected = Batch.objects.create(
            active=True,
            login_required=False,
            project=self.project
        )
        Task.objects.create(batch=batch_unprotected)
        self.assertEqual(len(Batch.access_permitted_for(anon_user)), 1)
        self.assertEqual(len(Batch.access_permitted_for(user)), 2)
        self.assertEqual(len(batch_unprotected.available_tasks_for(anon_user)), 1)
        self.assertEqual(
            Batch.available_task_counts_for(self.batch_query, anon_user)[batch_unprotected.id], 1)
        self.assertEqual(len(batch_unprotected.available_tasks_for(user)), 1)
        self.assertEqual(
            Batch.available_task_counts_for(self.batch_query, user)[batch_unprotected.id], 1)


class TestBatchReportFunctions(django.test.TestCase):
    def setUp(self):
        project = Project.objects.create(name='test')
        self.batch = Batch.objects.create(
            assignments_per_task=2,
            project=project,
        )
        self.task_1 = Task.objects.create(
            batch=self.batch,
            input_csv_fields={'number': '1', 'letter': 'a'}
        )
        self.task_2 = Task.objects.create(
            batch=self.batch,
            input_csv_fields={'number': '2', 'letter': 'b'}
        )
        self.user_1 = User.objects.create_user('user_1', password='secret')
        self.user_2 = User.objects.create_user('user_2', password='secret')

    def test_assignments_completed(self):
        self.assertEqual(self.batch.total_users_that_completed_tasks(), 0)
        ta_1 = TaskAssignment.objects.create(
            assigned_to=self.user_1,
            completed=False,
            task=self.task_1,
        )
        self.assertEqual(self.batch.total_users_that_completed_tasks(), 0)
        self.assertEqual(self.batch.total_assignments_completed_by(self.user_1), 0)
        self.assertEqual(self.batch.total_assignments_completed_by(self.user_2), 0)

        ta_1.completed = True
        ta_1.save()
        self.assertEqual(self.batch.total_users_that_completed_tasks(), 1)
        self.assertEqual(self.batch.users_that_completed_tasks()[0], self.user_1)
        self.assertEqual(self.batch.total_assignments_completed_by(self.user_1), 1)
        self.assertEqual(self.batch.assignments_completed_by(self.user_1)[0], ta_1)
        self.assertEqual(self.batch.total_assignments_completed_by(self.user_2), 0)

        ta_2 = TaskAssignment.objects.create(
            assigned_to=self.user_2,
            completed=True,
            task=self.task_1,
        )
        self.assertEqual(self.batch.total_users_that_completed_tasks(), 2)
        self.assertEqual(self.batch.assignments_completed_by(self.user_2)[0], ta_2)

    def test_work_time_in_seconds_stats(self):
        TaskAssignment.objects.create(
            assigned_to=self.user_1,
            completed=True,
            task=self.task_1,
        )
        TaskAssignment.objects.create(
            assigned_to=self.user_1,
            completed=True,
            task=self.task_1,
        )
        TaskAssignment.objects.create(
            assigned_to=self.user_1,
            completed=True,
            task=self.task_1,
        )
        self.batch.median_work_time_in_seconds()
        self.batch.mean_work_time_in_seconds()
        self.batch.total_work_time_in_seconds()

    def test_work_time_in_seconds_stats_with_no_completed_assignments(self):
        self.batch.median_work_time_in_seconds()
        self.batch.mean_work_time_in_seconds()
        self.batch.total_work_time_in_seconds()


class TestProject(django.test.TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')

    def test_copy_permissions_to_batches(self):
        project = Project.objects.create(
            custom_permissions=True,
            login_required=True,
        )
        group = Group.objects.create(name='testgroup')
        assign_perm('can_work_on', group, project)
        batch = Batch.objects.create(
            custom_permissions=False,
            login_required=False,
            project=project,
        )
        self.assertFalse('can_work_on_batch' in get_group_perms(group, batch))

        project.copy_permissions_to_batches()
        batch.refresh_from_db()
        self.assertTrue(batch.custom_permissions)
        self.assertTrue(batch.login_required)
        self.assertTrue('can_work_on_batch' in get_group_perms(group, batch))

    def test_copy_permissions_to_batches_unhydrated_project(self):
        # Verify that Project.copy_permissions_to_batches() works with
        # a Project model instance that is only "hydrated" with the
        # 'id' field.  Behavior related to this Issue:
        #
        #   https://github.com/hltcoe/turkle/issues/136

        project = Project.objects.create(
            custom_permissions=True,
            login_required=True,
        )
        group = Group.objects.create(name='testgroup')
        assign_perm('can_work_on', group, project)
        batch = Batch.objects.create(
            custom_permissions=False,
            login_required=False,
            project=project,
        )
        self.assertFalse('can_work_on_batch' in get_group_perms(group, batch))

        unhydrated_project = Project.objects.only('id', 'custom_permissions', 'login_required')\
                                            .get(id=project.id)
        unhydrated_project.copy_permissions_to_batches()
        batch.refresh_from_db()
        self.assertTrue(batch.custom_permissions)
        self.assertTrue(batch.login_required)
        self.assertTrue('can_work_on_batch' in get_group_perms(group, batch))

    def test_copy_permissions_to_batches_no_custom_permissions(self):
        project = Project.objects.create(
            custom_permissions=False,
            login_required=False,
        )
        group = Group.objects.create(name='testgroup')
        assign_perm('can_work_on', group, project)
        batch = Batch.objects.create(
            custom_permissions=True,
            login_required=True,
            project=project,
        )
        self.assertFalse('can_work_on_batch' in get_group_perms(group, batch))

        project.copy_permissions_to_batches()
        batch.refresh_from_db()
        self.assertFalse(batch.custom_permissions)
        self.assertFalse(batch.login_required)

        # Custom permissions are not copied from Project to Batch if
        # project.custom_permissions is False
        self.assertFalse('can_work_on_batch' in get_group_perms(group, batch))

    def test_form_with_submit_button(self):
        project = Project(
            name='Test',
            html_template='<p><input id="my_submit_button" type="submit" value="MySubmit" /></p>'
        )
        project.created_by = self.admin
        project.updated_by = self.admin
        save_model(project)
        self.assertTrue(project.html_template_has_submit_button)

    def test_form_without_submit_button(self):
        project = Project(
            name='Test',
            html_template='<p>Quick brown fox</p><textarea>'
        )
        project.created_by = self.admin
        project.updated_by = self.admin
        save_model(project)
        self.assertFalse(project.html_template_has_submit_button)

    def test_group_permissions(self):
        user = User.objects.create_user('testuser', password='secret')
        group = Group.objects.create(name='testgroup')
        user.groups.add(group)
        project = Project()
        project.save()

        # Group permissions are ignored if custom_permissions is False
        self.assertTrue(project.available_for(user))
        project.custom_permissions = True
        project.save()
        self.assertFalse(project.available_for(user))

        # Verify that giving the group access also gives the group members access
        self.assertFalse(user.has_perm('can_work_on', project))
        assign_perm('can_work_on', group, project)
        self.assertTrue(user.has_perm('can_work_on', project))
        self.assertTrue(project.available_for(user))

    def test_login_required_validation_1(self):
        # No ValidationError thrown
        Project(
            assignments_per_task=1,
            login_required=False,
            html_template='<textarea>'
        ).clean()

    def test_login_required_validation_2(self):
        # No ValidationError thrown
        Project(
            assignments_per_task=2,
            login_required=True,
            html_template='<textarea>'
        ).clean()

    def test_login_required_validation_3(self):
        with self.assertRaisesMessage(ValidationError, 'Assignments per Task must be 1'):
            Project(
                assignments_per_task=2,
                login_required=False,
                html_template='<textarea>'
            ).clean()

    def test_input_field_required(self):
        msg_part = "Please include at least one field"
        with self.assertRaisesRegex(ValidationError, msg_part):
            Project(
                assignments_per_task=2,
                login_required=True,
                html_template='<script>do stuff here</script>'
            ).clean()

    def test_too_large_template(self):
        limit = get_turkle_template_limit(True)
        template = 'a' * limit + '<textarea>'
        with self.assertRaisesMessage(ValidationError, 'Template is too large'):
            Project(
                html_template=template,
            ).clean()


class TestActiveProjectManager(django.test.TestCase):
    now = timezone.now()

    @staticmethod
    def create_project_with_assignment(completed, num_assignments=1):
        project = Project(name='test', html_template='<p>${number}</p><textarea>')
        project.save()
        batch = Batch(name='test', project=project)
        batch.save()
        task = Task(batch=batch, input_csv_fields={'number': '1'})
        task.save()
        for _ in range(num_assignments):
            TaskAssignment(
                assigned_to=None,
                completed=completed,
                task=task
            ).save()

    @mock.patch("django.utils.timezone.now")
    def test_get_queryset_filtering_projects_based_on_time(self, mock_now):
        manager = ActiveProjectManager()
        manager.model = ActiveProject
        mock_now.return_value = self.now
        self.create_project_with_assignment(True)
        mock_now.return_value = self.now - datetime.timedelta(days=2)
        self.create_project_with_assignment(True)

        mock_now.return_value = self.now
        self.assertEqual(1, len(manager.get_queryset(n_days=1)))
        self.assertEqual(2, len(manager.get_queryset(n_days=3)))

    @mock.patch("django.utils.timezone.now")
    def test_get_queryset_filtering_projects_based_on_completed(self, mock_now):
        manager = ActiveProjectManager()
        manager.model = ActiveProject
        mock_now.return_value = self.now
        self.create_project_with_assignment(True)
        self.create_project_with_assignment(False)

        self.assertEqual(1, len(manager.get_queryset(n_days=1)))

    @mock.patch("django.utils.timezone.now")
    def test_get_queryset_set_assignments(self, mock_now):
        manager = ActiveProjectManager()
        manager.model = ActiveProject
        mock_now.return_value = self.now
        self.create_project_with_assignment(True, num_assignments=3)

        project = manager.get_queryset(n_days=1)[0]
        self.assertEqual(3, project.completed_assignments())


class TestTask(django.test.TestCase):

    def setUp(self):
        """
        Sets up Project, Batch, Task objects, and saves them to the DB.
        The Project form HTML only displays the one input variable.
        The Task has inputs and answers and refers to the Project form.
        """
        admin = User.objects.create_superuser('admin', 'foo@bar.foo', 'secret')
        project = Project(name='test', html_template="<p>${foo}</p><textarea>")
        project.created_by = admin
        project.updated_by = admin
        save_model(project)
        batch = Batch(name='test', project=project, filename='test.csv')
        batch.created_by = admin
        batch.updated_by = admin
        save_model(batch)

        task = Task(
            batch=batch,
            input_csv_fields={'foo': 'bar'},
            completed=True,
        )
        task.save()
        self.task = task

        self.task_assignment = TaskAssignment(
            answers={
                "comment": "\u221e", "userDisplayLanguage": "",
                "sentence_textbox_3_verb1": "", "city": "",
                "sentence_textbox_1_verb6": "",
                "sentence_textbox_1_verb7": "",
                "sentence_textbox_1_verb4": "",
                "sentence_textbox_1_verb5": "",
                "sentence_textbox_1_verb2": "",
                "sentence_textbox_1_verb3": "",
                "sentence_textbox_1_verb1": "",
                "sentence_textbox_2_verb4": "",
                "csrfmiddlewaretoken": "7zxQ9Yyug6Nsnm4nLky9p8ObJwNipdu8",
                "sentence_drop_2_verb3": "foo",
                "sentence_drop_2_verb2": "foo",
                "sentence_drop_2_verb1": "foo",
                "sentence_textbox_2_verb1": "",
                "sentence_textbox_2_verb3": "",
                "sentence_drop_2_verb4": "foo",
                "sentence_textbox_2_verb2": "",
                "submitit": "Submit", "browserInfo": "",
                "sentence_drop_1_verb1": "foo",
                "sentence_drop_1_verb2": "foo",
                "sentence_drop_1_verb3": "foo",
                "sentence_drop_1_verb4": "foo",
                "sentence_drop_1_verb5": "foo",
                "sentence_drop_1_verb6": "foo",
                "sentence_drop_1_verb7": "foo", "country": "",
                "sentence_drop_3_verb1": "foo",
                "ipAddress": "", "region": ""
            },
            assigned_to=None,
            completed=True,
            task=task
        )
        self.task_assignment.save()

    def test_extract_fieldnames_from_form_html(self):
        self.assertEqual(
            {'foo': True},
            self.task.batch.project.fieldnames
        )

        project = Project(name='test', html_template='<p>${foo} - ${bar}</p><textarea>')
        project.clean()
        self.assertEqual(
            {'foo': True, 'bar': True},
            project.fieldnames
        )

    def test_new_task(self):
        """
        str(task) should return the template's title followed by :id of the
        task.
        """
        self.assertEqual('Task id:{}'.format(self.task.id), str(self.task))

    def test_result_to_dict_Answer(self):
        self.assertEqual(
            'foo',
            self.task_assignment.answers['sentence_drop_1_verb1']
        )

    def test_result_to_dict_ignore_csrfmiddlewaretoken(self):
        with self.assertRaises(KeyError):
            self.task_assignment.answers['Answer.csrfmiddlewaretoken']

    def test_result_to_dict_should_include_inputs(self):
        self.assertEqual(
            'foo',
            self.task_assignment.answers['sentence_drop_1_verb1']
        )

    def test_result_to_dict_unicode(self):
        self.assertEqual(
            '∞',
            self.task_assignment.answers['comment']
        )


class TestGenerateForm(django.test.TestCase):
    """Tests generating the form for a Task from the template and csv data"""
    def setUp(self):
        with open('turkle/tests/resources/form_0.html') as f:
            html_template = f.read()

        self.project = Project(name="filepath", html_template=html_template)
        self.project.save()
        self.batch = Batch(project=self.project)
        self.batch.save()
        field_names = "tweet0_id,tweet0_entity,tweet0_before_entity,tweet0_after_entity," + \
            "tweet0_word0,tweet0_word1,tweet0_word2,tweet1_id,tweet1_entity," + \
            "tweet1_before_entity,tweet1_after_entity,tweet1_word0,tweet1_word1,tweet1_word2," + \
            "tweet2_id,tweet2_entity,tweet2_before_entity,tweet2_after_entity,tweet2_word0," + \
            "tweet2_word1,tweet2_word2,tweet3_id,tweet3_entity,tweet3_before_entity," + \
            "tweet3_after_entity,tweet3_word0,tweet3_word1,tweet3_word2,tweet4_id," + \
            "tweet4_entity,tweet4_before_entity,tweet4_after_entity,tweet4_word0," + \
            "tweet4_word1,tweet4_word2,tweet5_id,tweet5_entity,tweet5_before_entity," + \
            "tweet5_after_entity,tweet5_word0,tweet5_word1,tweet5_word2",
        values = "268,SANTOS, Muy bien America ......... y lo siento mucho , un muy buen " + \
            "rival,mucho,&nbsp;,&nbsp;,2472,GREGORY, Ah bueno , tampoco andes pidiendo ese " +\
            "tipo de milagros . @jcabrerac @CarlosCabreraR,bueno,&nbsp;,&nbsp;,478,ALEJANDRO," + \
            " @aguillen19 &#44; un super abrazo mi querido , &#44; mis mejores deseos para " + \
            "este 2012 ... muakkk !,querido,&nbsp;,&nbsp;,906_control, PF, Acusan camioneros " + \
            "extorsiones de, : Transportistas acusaron que deben pagar entre 13 y 15 mil " + \
            "pesos a agentes que .. http://t.co/d8LUVvhP,acusaron,&nbsp;,&nbsp;,2793_control," + \
            " CHICARO, Me gusta cuando chicharo hace su oracion es lo que lo hace especial .," + \
            "&nbsp;,gusta,&nbsp;,&nbsp;,357,OSCAR WILDE&QUOT;, &quot; @ ifilosofia : Las " + \
            "pequeñas acciones de cada día son las que hacen o deshacen el carácter.&quot; , " + \
            "bueno !!!! Es así,bueno,&nbsp;,&nbsp;",
        self.task = Task(
            batch=self.batch,
            input_csv_fields=dict(zip(field_names, values))
        )
        self.task.save()

    def test_populate_html_template(self):
        with open('turkle/tests/resources/form_0_filled.html') as f:
            form = f.read()

        expect = form
        actual = self.task.populate_html_template()
        self.assertNotEqual(expect, actual)

    def test_map_fields_csv_row(self):
        project = Project(
            name='test',
            html_template="""</select> con relaci&oacute;n a """ +
            """<span style="color: rgb(0, 0, 255);">""" +
            """${tweet0_entity}</span> en este mensaje.</p><textarea>"""
        )
        project.save()
        batch = Batch(project=project)
        batch.save()
        task = Task(
            batch=batch,
            input_csv_fields=dict(
                zip(
                    ["tweet0_id", "tweet0_entity"],
                    ["268", "SANTOS"],
                )
            ),
        )
        task.save()
        expect = """</select> con relaci&oacute;n a <span style="color:""" + \
            """ rgb(0, 0, 255);">SANTOS</span> en este mensaje.</p><textarea>"""
        actual = task.populate_html_template()
        self.assertEqual(expect, actual)


class TestTaskAssignment(django.test.TestCase):
    def test_task_marked_as_completed(self):
        # When assignment_per_task==1, completing 1 Assignment marks Task as complete
        project = Project(name='test', html_template='<p>${number} - ${letter}</p><textarea>')
        project.save()
        batch = Batch(name='test', project=project)
        batch.save()

        task = Task(
            batch=batch,
            input_csv_fields={'number': '1', 'letter': 'a'}
        )
        task.save()

        self.assertEqual(batch.assignments_per_task, 1)
        self.assertFalse(task.completed)
        self.assertFalse(batch.completed)

        TaskAssignment(
            assigned_to=None,
            completed=True,
            task=task
        ).save()

        task.refresh_from_db()
        batch.refresh_from_db()
        self.assertTrue(task.completed)
        self.assertTrue(batch.completed)

    def test_task_marked_as_completed_two_way_redundancy(self):
        # When assignment_per_task==2, completing 2 Assignments marks Task as complete
        project = Project(name='test', html_template='<p>${number} - ${letter}</p><textarea>')
        project.save()
        batch = Batch(name='test', project=project)
        batch.assignments_per_task = 2
        batch.save()

        task = Task(
            batch=batch,
            input_csv_fields={'number': '1', 'letter': 'a'}
        )
        task.save()
        self.assertFalse(task.completed)
        self.assertFalse(batch.completed)

        TaskAssignment(
            assigned_to=None,
            completed=True,
            task=task
        ).save()
        task.refresh_from_db()
        batch.refresh_from_db()
        self.assertFalse(task.completed)
        self.assertFalse(batch.completed)

        TaskAssignment(
            assigned_to=None,
            completed=True,
            task=task
        ).save()
        task.refresh_from_db()
        batch.refresh_from_db()
        self.assertTrue(task.completed)
        self.assertTrue(batch.completed)

    def test_expire_all_abandoned(self):
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
        TaskAssignment.expire_all_abandoned()
        self.assertEqual(TaskAssignment.objects.count(), 0)

    def test_expire_all_abandoned__dont_delete_completed(self):
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
            completed=True,
            expires_at=past,
            task=task,
        )
        # Bypass TaskAssignment's save(), which updates expires_at
        super(TaskAssignment, ha).save()
        self.assertEqual(TaskAssignment.objects.count(), 1)
        TaskAssignment.expire_all_abandoned()
        self.assertEqual(TaskAssignment.objects.count(), 1)

    def test_expire_all_abandoned__dont_delete_non_expired(self):
        t = timezone.now()
        dt = datetime.timedelta(hours=2)
        future = t + dt

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
            expires_at=future,
            task=task,
        )
        # Bypass TaskAssignment's save(), which updates expires_at
        super(TaskAssignment, ha).save()
        self.assertEqual(TaskAssignment.objects.count(), 1)
        TaskAssignment.expire_all_abandoned()
        self.assertEqual(TaskAssignment.objects.count(), 1)

    def test_work_time_in_seconds(self):
        project = Project.objects.create()
        batch = Batch.objects.create(project=project)
        task = Task.objects.create(batch=batch)
        ta = TaskAssignment.objects.create(task=task)

        em = 'Cannot compute work_time_in_seconds for incomplete TaskAssignment %d' % ta.id
        with self.assertRaisesMessage(ValueError, em):
            ta.work_time_in_seconds()

        ta.completed = True
        ta.save()
        self.assertEqual(float(ta.work_time_in_seconds()).is_integer(), True)

    def test_expire_time_not_updated_when_completed(self):
        # expire_at should only be set when created, not when assignment submitted
        project = Project.objects.create()
        batch = Batch.objects.create(project=project)
        task = Task.objects.create(batch=batch)
        ta = TaskAssignment.objects.create(task=task)
        expire_time = ta.expires_at
        time.sleep(0.01)

        ta.completed = True
        ta.save()
        self.assertEqual(expire_time, ta.expires_at)
