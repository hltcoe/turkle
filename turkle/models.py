import csv
import ctypes
from datetime import timedelta
import logging
import os.path
import re
import statistics
import sys

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, IntegerField, Max, Q, OuterRef, Prefetch, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone
from guardian.core import ObjectPermissionChecker
from guardian.models import GroupObjectPermission
from guardian.shortcuts import assign_perm, get_group_perms, get_groups_with_perms, \
    get_user_perms, get_users_with_perms
from jsonfield import JSONField

from .utils import get_turkle_template_limit

User = get_user_model()

logger = logging.getLogger(__name__)

C_LONG_NUM_BITS = 8 * ctypes.sizeof(ctypes.c_long)
C_LONG_MAX = 2 ** (C_LONG_NUM_BITS-1) - 1

# Increase default field size limit (default 131072 characters).
# Note that field_size_limit converts its argument to a C long,
# at least in Anaconda 3 on Windows 10.
csv.field_size_limit(min(C_LONG_MAX, sys.maxsize))


class ActiveUserManager(models.Manager):
    """Query users by activity on assignments"""
    def get_queryset(self, **kwargs):
        # adds annotations for number of assignments and most recent assignment time
        n_days = int(kwargs.get('n_days', 7))
        time_cutoff = timezone.now() - timedelta(days=n_days)
        active_users = super().get_queryset(). \
            filter(Q(taskassignment__updated_at__gt=time_cutoff) &
                   Q(taskassignment__completed=True)). \
            distinct(). \
            annotate(
                total_assignments=Count('taskassignment',
                                        filter=(Q(taskassignment__updated_at__gt=time_cutoff) &
                                                Q(taskassignment__completed=True)))). \
            annotate(last_finished_time=Max('taskassignment__updated_at',
                                            filter=Q(taskassignment__completed=True)))
        return active_users


class ActiveUser(User):
    """Proxy object for User that provides fields related to assignments.

    The values for the additional fields come from annotations set by the manager.
    """
    objects = ActiveUserManager()

    class Meta:
        proxy = True
        ordering = ['first_name']

    def name(self):
        return f"{self.first_name} {self.last_name}"
    name.admin_order_field = 'first_name'

    def completed_assignments(self):
        return self.total_assignments
    completed_assignments.admin_order_field = 'total_assignments'

    def most_recent(self):
        return self.last_finished_time
    most_recent.admin_order_field = 'last_finished_time'


class TaskAssignmentStatistics(object):
    """Mixin class for Batch/Project that computes TaskAssignment statistics

    Assumes that the inheriting class has a finished_task_assignments()
    method that returns a QuerySet of TaskAssignments.
    """
    def mean_work_time_in_seconds(self):
        """
        Returns:
            Float for mean work time (in seconds) for completed Tasks in this Batch
        """
        finished_assignments = self.finished_task_assignments()
        if finished_assignments.count() > 0:
            return statistics.mean(
                [ta.work_time_in_seconds() for ta in self.finished_task_assignments()])
        else:
            return 0

    def median_work_time_in_seconds(self):
        """
        Returns:
            Integer for median work time (in seconds) for completed Tasks in this Batch
        """
        if self.finished_task_assignments().count() > 0:
            # np.median returns float but we convert back to int computed by work_time_in_seconds()
            return int(statistics.median(
                [ta.work_time_in_seconds() for ta in self.finished_task_assignments()]
            ))
        else:
            return 0

    def total_work_time_in_seconds(self):
        """
        Returns:
            Integer sum of work_time_in_seconds() for all completed
            TaskAssignments in this Batch
        """
        return sum([ta.work_time_in_seconds() for ta in self.finished_task_assignments()])


class Task(models.Model):
    """Human Intelligence Task
    """
    class Meta:
        verbose_name = "Task"

    batch = models.ForeignKey('Batch', on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    input_csv_fields = JSONField()

    def __str__(self):
        return 'Task id:{}'.format(self.id)

    def populate_html_template(self):
        """Return HTML template for this Task's project, with populated template variables

        Returns:
            String containing the HTML template for the Project associated with
            this Task, with all template variables replaced with the template
            variable values stored in this Task's input_csv_fields.
        """
        result = self.batch.project.html_template
        for field in self.input_csv_fields.keys():
            result = result.replace(
                r'${' + field + r'}',
                self.input_csv_fields[field]
            )
        return result


class TaskAssignment(models.Model):
    """Task Assignment
    """
    class Meta:
        verbose_name = "Task Assignment"

    answers = JSONField(blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True, null=True,
                                    on_delete=models.CASCADE)
    completed = models.BooleanField(db_index=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    @classmethod
    def expire_all_abandoned(cls):
        result = cls.objects.\
            filter(completed=False).\
            filter(expires_at__lt=timezone.now()).\
            delete()
        if result[0]:
            logger.info('Expired %i task assignments', result[0])
        return result

    def save(self, *args, **kwargs):
        # set expires_at only when assignment is created
        if not self.id:
            self.expires_at = timezone.now() + \
                timedelta(hours=self.task.batch.allotted_assignment_time)

        if 'csrfmiddlewaretoken' in self.answers:
            del self.answers['csrfmiddlewaretoken']
        super().save(*args, **kwargs)

        # Mark Task as completed if all Assignments have been completed
        if self.task.taskassignment_set.filter(completed=True).count() >= \
           self.task.batch.assignments_per_task:
            self.task.completed = True
            self.task.save()

        # Mark Batch as completed if all Tasks have been completed
        self.task.batch.update_completed_status()

    def work_time_in_seconds(self):
        """Return number of seconds elapsed between Task assignment and submission

        We compute the time elapsed in Python instead of in SQL
        because "there are no native date/time fields in SQLite and
        Django currently emulates these features using a text field,"
        per the Django Docs:
          https://docs.djangoproject.com/en/3.1/ref/models/querysets/#aggregation-functions

        Returns:
            Integer for seconds elapsed between Task assignment and submission

        Raises:
            ValueError if TaskAssignment is not completed
        """
        if self.completed:
            return int((self.updated_at - self.created_at).total_seconds())
        else:
            raise ValueError(
                'Cannot compute work_time_in_seconds for incomplete TaskAssignment %d' %
                self.id)


class Batch(TaskAssignmentStatistics, models.Model):
    class Meta:
        permissions = (
            ('can_work_on_batch', 'Can work on Tasks for this Batch'),
        )
        verbose_name = "Batch"
        verbose_name_plural = "Batches"

    active = models.BooleanField(db_index=True, default=True)
    allotted_assignment_time = models.IntegerField(default=24)
    assignments_per_task = models.IntegerField(default=1, verbose_name='Assignments per Task')
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                   related_name='created_batches', on_delete=models.CASCADE,
                                   verbose_name='creator')
    custom_permissions = models.BooleanField(default=False)
    filename = models.CharField(max_length=1024)
    login_required = models.BooleanField(db_index=True, default=True)
    name = models.CharField(max_length=1024)
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    published = models.BooleanField(db_index=True, default=True)

    @classmethod
    def access_permitted_for(cls, user):
        """Retrieve the active Batches that the user has permission to access

        Both the Batch and the Project associated the Batch must be active.

        Args:
            user (User):

        Returns:
            List of Batch objects this user can access
        """
        batches = cls.objects.filter(active=True).filter(published=True)\
            .filter(project__active=True)
        if not user.is_authenticated:
            batches = batches.filter(login_required=False)

        # Can implement our own prefetch_perms() in future for efficiency
        checker = TurklePermissionChecker(user)
        checker.prefetch_perms(batches)

        return [b for b in batches if checker.has_perm('can_work_on_batch', b)]

    @classmethod
    def available_task_counts_for(cls, batch_query, user):
        """Retrieve # of tasks available for user for the Batches in query

        Args:
            batch_query (QuerySet): A QuerySet that retrieves Batch objects
            user (User):

        Returns:
            Dict where keys are Batch IDs (int) and values are the total
            number of tasks in the batch available for the specified user.
        """
        available_task_counts = {}

        # Completed batches (in the original batch_query) have an available task count of 0
        for b_id in batch_query.filter(completed=True).values_list('id', flat=True):
            available_task_counts[b_id] = 0

        if not user.is_authenticated:
            # Batches an anonymous user does not have access to have an available task count of 0
            for b_id in batch_query.filter(login_required=True).values_list('id', flat=True):
                available_task_counts[b_id] = 0
            batch_query = batch_query.exclude(login_required=True)

        # Count number of tasks available for case where Batch.assignments_per_task == 1
        # For this case, the number of available tasks is the same for all users with
        # access to the batch.
        oneway_batch_query = batch_query.filter(assignments_per_task=1).filter(completed=False)
        unassigned_tasks = Task.objects.filter(completed=False).filter(taskassignment=None)

        # Django does not easily support aggregations (such as Count) using subqueries:
        #   https://code.djangoproject.com/ticket/28296
        # The Django documentation states that:
        #  "Aggregates may be used within a Subquery, but they require a specific
        #   combination of filter(), values(), and annotate() to get the subquery
        #   grouping correct."
        #     https://docs.djangoproject.com/en/3.1/ref/models/expressions/#using-aggregates-within-a-subquery-expression
        # The specific syntax we use here for count subqueries is adapted from:
        #   https://github.com/martsberger/django-sql-utils
        # where we are using the pattern:
        #   subquery = Subquery(Child.objects.filter(parent_id=OuterRef('id')).order_by()
        #                      .values('parent').annotate(count=Count('pk'))
        #                      .values('count'), output_field=IntegerField())
        #   Parent.objects.annotate(child_count=Coalesce(subquery, 0))
        task_count_subquery = Subquery(
            unassigned_tasks
            .filter(batch=OuterRef('pk'))
            .order_by().values('batch').annotate(count=Count('pk')).values('count'),
            output_field=IntegerField())

        oneway_batch_values = oneway_batch_query\
            .annotate(available_task_count=Coalesce(task_count_subquery, 0))\
            .values('available_task_count', 'id')
        for obv in oneway_batch_values:
            available_task_counts[obv['id']] = obv['available_task_count']

        multiway_batch_query = batch_query.filter(assignments_per_task__gt=1)\
                                          .filter(completed=False)
        if user.is_authenticated:
            # Count number of tasks available for case where Batch.assignments_per_task > 1
            ta_count_subquery = Subquery(
                TaskAssignment.objects
                .filter(task=OuterRef('pk'))
                .order_by().values('task').annotate(count=Count('pk')).values('count'),
                output_field=IntegerField())
            unassigned_tasks = Task.objects.filter(completed=False)\
                                           .annotate(ac=Coalesce(ta_count_subquery, 0))\
                                           .filter(ac__lt=OuterRef('assignments_per_task'))\
                                           .exclude(taskassignment__assigned_to=user)
            task_count_subquery = Subquery(
                unassigned_tasks
                .filter(batch=OuterRef('pk'))
                .order_by().values('batch').annotate(count=Count('pk')).values('count'),
                output_field=IntegerField())
            multiway_batch_values = multiway_batch_query\
                .annotate(available_task_count=Coalesce(task_count_subquery, 0))\
                .values('available_task_count', 'id')
            for mbv in multiway_batch_values:
                available_task_counts[mbv['id']] = mbv['available_task_count']
        else:
            # Only authenticated users should have access to multiple-assignment batches
            # If the database somehow contains multiple-assignment Batches that are
            # accessible to an anonymous user, we set the available task count to 0
            for mbv in multiway_batch_query.values('id'):
                available_task_counts[mbv['id']] = 0

        return available_task_counts

    def assignments_completed_by(self, user):
        """
        Returns:
            QuerySet of all TaskAssignments completed by specified user
            that are part of this Batch
        """
        return TaskAssignment.objects.\
            filter(completed=True).\
            filter(assigned_to_id=user.id).\
            filter(task__batch=self)

    def available_for(self, user):
        """
        Returns:
            Boolean indicating if this Batch is available for the user
        """
        if not self.active or \
           not self.project.active or \
           (not user.is_authenticated and self.login_required):
            return False
        elif self.custom_permissions:
            return user.has_perm('can_work_on_batch', self)
        else:
            return True

    def available_tasks_for(self, user):
        """Retrieve a list of all Tasks in this Batch available for the user.

        This list DOES NOT include Tasks in the Batch that have been assigned
        to the user but not yet completed.

        Args:
            user (User|AnonymousUser):

        Returns:
            QuerySet of available Task objects
        """
        if not self.available_for(user):
            return Task.objects.none()

        hs = self.task_set.filter(completed=False)

        if self.assignments_per_task > 1:
            # Exclude Tasks that have already been assigned to this user.
            if user.is_authenticated:
                # If the user is not authenticated, then user.id is None,
                # and the query below would exclude all uncompleted Tasks.
                hs = hs.exclude(taskassignment__assigned_to_id=user.id)

            # Only include Tasks when # of (possibly incomplete) assignments < assignments_per_task
            hs = hs.annotate(ac=models.Count('taskassignment')).\
                filter(ac__lt=self.assignments_per_task)
        elif self.assignments_per_task == 1:
            # Only returns Tasks that have not been assigned to anyone (including this user)
            hs = hs.filter(taskassignment=None)

        return hs

    def available_task_ids_for(self, user):
        return self.available_tasks_for(user).values_list('id', flat=True)

    def clean(self):
        if not self.login_required and self.assignments_per_task != 1:
            raise ValidationError('When login is not required to access a Batch, ' +
                                  'the number of Assignments per Task must be 1')

    def copy_project_permissions(self):
        """Copy 'permission' settings from associated Project to this Batch

        Copies:
        - `custom_permissions` flag
        - `login_required` flag
        - group-level access permissions
        """
        self.custom_permissions = self.project.custom_permissions
        self.login_required = self.project.login_required
        if self.custom_permissions:
            for group in get_groups_with_perms(self.project):
                if 'can_work_on' in get_group_perms(group, self.project):
                    assign_perm('can_work_on_batch', group, self)

    def csv_results_filename(self):
        """Returns filename for CSV results file for this Batch
        """
        batch_filename, extension = os.path.splitext(os.path.basename(self.filename))

        # We are deviating from Mechanical Turk's naming conventions for results files
        return "Project-{}_Batch-{}-{}_results{}".format(
            self.project.id, self.id, batch_filename, extension)

    def create_tasks_from_csv(self, csv_fh):
        """
        Args:
            csv_fh (file-like object): File handle for CSV input

        Returns:
            Number of Tasks created from CSV file
        """
        header, data_rows = self._parse_csv(csv_fh)

        logger.info('Creating tasks for Batch(%i) %s', self.id, self.name)
        num_created_tasks = 0
        for row in data_rows:
            if not row:
                continue
            task = Task(
                batch=self,
                input_csv_fields=dict(zip(header, row)),
            )
            task.save()
            num_created_tasks += 1
        logger.info('Created %i tasks for Batch(%i) %s', num_created_tasks, self.id, self.name)

        return num_created_tasks

    def finished_tasks(self):
        """
        Returns:
            QuerySet of all Task objects associated with this Batch
            that have been completed.
        """
        return self.task_set.filter(completed=True).order_by('-id')

    def finished_task_assignments(self):
        """
        Returns:
            QuerySet of all Task Assignment objects associated with this Batch
            that have been completed.
        """
        return TaskAssignment.objects.filter(task__batch_id=self.id)\
                                     .filter(completed=True)

    def get_user_custom_permissions(self):
        """Get users who have a can_work_on_batch permission"""
        users = []
        for user in get_users_with_perms(self):
            if 'can_work_on_batch' in get_user_perms(user, self):
                users.append(user)
        return users

    def get_group_custom_permissions(self):
        """Get groups that have a can_work_on_batch permission"""
        groups = []
        for group in get_groups_with_perms(self):
            if 'can_work_on_batch' in get_group_perms(group, self):
                groups.append(group)
        return groups

    def is_active(self):
        return self.active and self.published
    is_active.short_description = 'Active'
    is_active.boolean = True

    def next_available_task_for(self, user):
        """Returns next available Task for the user, or None if no Tasks available

        Args:
            user (User):

        Returns:
            Task|None
        """
        return self.available_tasks_for(user).first()

    def total_assignments_completed_by(self, user):
        """
        Returns:
            Integer of total number of TaskAssignments completed by
            specified user that are part of this Batch
        """
        return self.assignments_completed_by(user).count()

    def total_available_tasks_for(self, user):
        """Returns number of Tasks available for the user

        Args:
            user (User):

        Returns:
            Number of Tasks available for user
        """
        return self.available_tasks_for(user).count()

    def total_finished_tasks(self):
        return self.finished_tasks().count()
    total_finished_tasks.short_description = 'Total finished Tasks'

    def total_finished_task_assignments(self):
        return self.finished_task_assignments().count()
    total_finished_task_assignments.short_description = 'Total finished Task Assignments'

    def total_task_assignments(self):
        return self.assignments_per_task * self.total_tasks()

    def total_tasks(self):
        return self.task_set.count()
    total_tasks.short_description = 'Total Tasks'

    def total_users_that_completed_tasks(self):
        """
        Returns:
            Integer counting number of Users that have completed
            TaskAssignments that are part of this Batch
        """
        return self.users_that_completed_tasks().count()

    def to_csv(self, csv_fh, lineterminator='\r\n'):
        """Write CSV output to file handle for every Task in batch

        Args:
            csv_fh (file-like object): File handle for CSV output
        """
        fieldnames, rows = self._results_data(self.task_set.all())
        writer = csv.DictWriter(csv_fh, fieldnames, lineterminator=lineterminator,
                                quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    def to_input_csv(self, csv_fh, lineterminator='\r\n'):
        """Write (reconstructed) CSV input to file handle for every Task in Batch

        PLEASE NOTE: The column order in the reconstructed CSV file
        may not match the column order in the original CSV file.
        """
        tasks = self.task_set.all()
        if not tasks.exists():
            return

        # Some rows may (theoretically) be missing fields
        fieldnames = set()
        for task in tasks:
            fieldnames.update(task.input_csv_fields.keys())

        writer = csv.DictWriter(csv_fh, list(fieldnames), lineterminator=lineterminator,
                                quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for task in tasks:
            writer.writerow(task.input_csv_fields)

    def unfinished_task_assignments(self):
        """
        Returns:
            QuerySet of all Task Assignment objects associated with this Batch
            that have not been completed.
        """
        return TaskAssignment.objects.filter(task__batch_id=self.id)\
                                     .filter(completed=False)

    def unfinished_tasks(self):
        """
        Returns:
            QuerySet of all Task objects associated with this Batch
            that have NOT been completed.
        """
        return self.task_set.filter(completed=False).order_by('id')

    def update_completed_status(self):
        """Update the `completed` flag to match the Batch completed status

        A Batch is marked "complete" IFF all of the Batch's Tasks are marked as `completed`.

        A database write occurs IFF the "completed" status has changed since the `completed`
        flag was last updated.
        """
        completed_status = not self.unfinished_tasks().exists()
        if self.completed != completed_status:
            self.completed = completed_status
            self.save()

    def users_that_completed_tasks(self):
        """
        Returns:
            QuerySet of all Users who have completed TaskAssignments
            that are part of this Batch
        """
        return User.objects.\
            filter(taskassignment__task__batch=self).\
            filter(taskassignment__completed=True).\
            distinct()

    def _parse_csv(self, csv_fh):
        """
        Args:
            csv_fh (file-like object): File handle for CSV output

        Returns:
            A tuple where the first value is a list of strings for the
            header fieldnames, and the second value is an iterable
            that returns a list of values for the rest of the row in
            the CSV file.
        """
        rows = csv.reader(csv_fh)
        header = next(rows)
        return header, rows

    def _get_csv_fieldnames(self, task_queryset):
        """
        Args:
            task_queryset (QuerySet):

        Returns:
            A tuple of strings specifying the fieldnames to be used in
            in the header of a CSV file.
        """
        input_field_set = set()
        answer_field_set = set()
        task_assignments = TaskAssignment.objects.\
            filter(task__in=task_queryset).\
            prefetch_related(Prefetch('task', queryset=task_queryset))
        for task_assignment in task_assignments:
            input_field_set.update(task_assignment.task.input_csv_fields.keys())

            # If the answers JSONField is empty, it evaluates as a string instead of a dict
            if task_assignment.answers != '':
                answer_field_set.update(task_assignment.answers.keys())
        return tuple(
            ['HITId', 'HITTypeId', 'Title', 'CreationTime', 'MaxAssignments',
             'AssignmentDurationInSeconds', 'AssignmentId', 'WorkerId',
             'AcceptTime', 'SubmitTime', 'WorkTimeInSeconds'] +
            ['Input.' + k for k in sorted(input_field_set)] +
            ['Answer.' + k for k in sorted(answer_field_set)] +
            ['Turkle.Username']
        )

    def _results_data(self, task_queryset):
        """
        All completed Tasks must come from the same project so that they have the
        same field names.

        Args:
            task_queryset (QuerySet):

        Returns:
            A tuple where the first value is a list of fieldname strings, and
            the second value is a list of dicts, where the keys to these
            dicts are the values of the fieldname strings.
        """
        rows = []
        time_format = '%a %b %d %H:%M:%S %Z %Y'
        task_assignments = TaskAssignment.objects.\
            filter(task__in=task_queryset).\
            filter(completed=True).\
            prefetch_related(Prefetch('task', queryset=task_queryset))
        for task_assignment in task_assignments:
            task = task_assignment.task
            batch = task.batch
            project = task.batch.project

            if task_assignment.assigned_to:
                username = task_assignment.assigned_to.username
            else:
                username = ''

            row = {
                'HITId': task.id,
                'HITTypeId': project.id,
                'Title': project.name,
                'CreationTime': batch.created_at.strftime(time_format),
                'MaxAssignments': batch.assignments_per_task,
                'AssignmentDurationInSeconds': batch.allotted_assignment_time * 3600,
                'AssignmentId': task_assignment.id,
                'WorkerId': task_assignment.assigned_to_id,
                'AcceptTime': task_assignment.created_at.strftime(time_format),
                'SubmitTime': task_assignment.updated_at.strftime(time_format),
                'WorkTimeInSeconds': task_assignment.work_time_in_seconds(),
                'Turkle.Username': username,
            }
            row.update({'Input.' + k: v for k, v in task.input_csv_fields.items()})
            row.update({'Answer.' + k: v for k, v in task_assignment.answers.items()})
            rows.append(row)

        return self._get_csv_fieldnames(task_queryset), rows

    def __str__(self):
        return 'Batch: {}'.format(self.name)


class TurklePermissionChecker(ObjectPermissionChecker):
    """
    Wrapper for django-guardian's permissions checker.

    Handles projects that don't have custom permissions.
    """

    def has_perm(self, perm, obj):
        """
        Checks if user/group has given permission for object.
        :param perm: permission as string, may or may not contain app_label
          prefix (if not prefixed, we grab app_label from ``obj``)
        :param obj: Django model instance for which permission should be checked
        """
        if self.user and not self.user.is_active:
            return False
        elif self.user and self.user.is_superuser:
            return True
        elif not self.user.is_authenticated and obj.login_required:
            return False
        elif obj.custom_permissions:
            if '.' in perm:
                _, perm = perm.split('.', 1)
            return perm in self.get_perms(obj)
        else:
            return True


class Project(TaskAssignmentStatistics, models.Model):
    class Meta:
        permissions = (
            # For consistency with Django Guardian naming conventions
            # ('{VERB}_{MODELNAME}'), this permission SHOULD have been
            # named 'can_work_on_project'
            ('can_work_on', 'Can work on Tasks for this Project'),
        )
        verbose_name = "Project"
        ordering = ['-id']

    active = models.BooleanField(db_index=True, default=True)
    allotted_assignment_time = models.IntegerField(default=24)
    assignments_per_task = models.IntegerField(db_index=True, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                   related_name='created_projects',
                                   on_delete=models.CASCADE, verbose_name='creator')
    custom_permissions = models.BooleanField(default=False)
    filename = models.CharField(max_length=1024, blank=True)
    html_template = models.TextField()
    html_template_has_submit_button = models.BooleanField(default=False)
    login_required = models.BooleanField(db_index=True, default=True)
    name = models.CharField(max_length=1024)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                   related_name='updated_projects',
                                   on_delete=models.CASCADE)

    # Fieldnames are automatically extracted from html_template text
    fieldnames = JSONField(blank=True)

    def assignments_completed_by(self, user):
        """
        Returns:
            QuerySet of all TaskAssignments completed by specified user
            that are part of this Project
        """
        return TaskAssignment.objects.\
            filter(completed=True).\
            filter(assigned_to_id=user.id).\
            filter(task__batch__project=self)

    def available_for(self, user):
        """
        Returns:
            Boolean indicating if this Project is available for the user
        """
        if not user.is_authenticated and self.login_required:
            return False
        elif self.custom_permissions:
            return user.has_perm('can_work_on', self)
        else:
            return True

    def clean(self):
        # duplicated in ProjectSerializer
        super().clean()
        if len(self.html_template) > get_turkle_template_limit(True):
            raise ValidationError({'html_template': 'Template is too large'}, code='invalid')
        if not self.login_required and self.assignments_per_task != 1:
            raise ValidationError('When login is not required to access the Project, ' +
                                  'the number of Assignments per Task must be 1')
        self.process_template()

    def process_template(self):
        # duplicated in ProjectSerializer
        soup = BeautifulSoup(self.html_template, 'html.parser')
        self.html_template_has_submit_button =\
            bool(soup.select('input[type=submit], button[type=submit]'))

        # Extract fieldnames from html_template text, save fieldnames as keys of JSON dict
        unique_fieldnames = set(re.findall(r'\${(\w+)}', self.html_template))
        self.fieldnames = dict((fn, True) for fn in unique_fieldnames)

        # Matching mTurk we confirm at least one input, select, or textarea
        if soup.find('input') is None and soup.find('select') is None \
                and soup.find('textarea') is None:
            msg = "Template does not contain any fields for responses. " + \
                  "Please include at least one field (input, select, or textarea)." + \
                  "This usually means you are generating HTML with JavaScript." + \
                  "If so, add an unused hidden input."
            raise ValidationError({'html_template': msg}, code='invalid')

    def get_user_custom_permissions(self):
        """Get users who have a can_work_on permission to the project"""
        users = []
        for user in get_users_with_perms(self):
            if 'can_work_on' in get_user_perms(user, self):
                users.append(user)
        return users

    def get_group_custom_permissions(self):
        """Get groups that have a can_work_on permission to the project"""
        groups = []
        for group in get_groups_with_perms(self):
            if 'can_work_on' in get_group_perms(group, self):
                groups.append(group)
        return groups

    def copy_permissions_to_batches(self):
        """Copy permissions from this Project to all associated Batches

        Copies:
        - `custom_permissions` flag
        - `login_required` flag
        - group-level access permissions
        """
        self.batch_set.update(
            custom_permissions=self.custom_permissions,
            login_required=self.login_required,
        )
        if self.custom_permissions:
            for group in get_groups_with_perms(self):
                if 'can_work_on' in get_group_perms(group, self):
                    batches = self.batch_set.all()
                    GroupObjectPermission.objects.bulk_assign_perm(
                        'can_work_on_batch', group, batches)

    def finished_task_assignments(self):
        """
        Returns:
            QuerySet of all Task Assignment objects associated with this Project
            that have been completed.
        """
        return TaskAssignment.objects.filter(task__batch__project_id=self.id)\
                                     .filter(completed=True)

    def total_assignments_completed_by(self, user):
        """
        Returns:
            Integer of total number of TaskAssignments completed by
            specified user that are part of this Project
        """
        return self.assignments_completed_by(user).count()

    def users_that_completed_tasks(self):
        """
        Returns:
            QuerySet of all Users who have completed TaskAssignments
            that are part of this Project
        """
        return User.objects.\
            filter(taskassignment__task__batch__project=self).\
            filter(taskassignment__completed=True).\
            distinct()

    def __str__(self):
        return self.name


class ActiveProjectManager(models.Manager):
    """Query projects by activity on assignments"""
    def get_queryset(self, **kwargs):
        n_days = int(kwargs.get('n_days', 7))
        time_cutoff = timezone.now() - timedelta(days=n_days)
        return super().get_queryset().\
            filter(Q(batch__task__taskassignment__updated_at__gt=time_cutoff) &
                   Q(batch__task__taskassignment__completed=True)).\
            distinct().\
            annotate(assignments=Count(
                'batch__task__taskassignment',
                filter=(Q(batch__task__taskassignment__updated_at__gt=time_cutoff) &
                        Q(batch__task__taskassignment__completed=True)))).\
            annotate(last_finished_time=Max(
                'batch__task__taskassignment__updated_at',
                filter=Q(batch__task__taskassignment__completed=True)))


class ActiveProject(Project):
    """Proxy object for Project using annotations from its manager"""
    objects = ActiveProjectManager()

    class Meta:
        proxy = True
        ordering = ['name']

    def completed_assignments(self):
        return self.assignments
    completed_assignments.admin_order_field = 'assignments'

    def most_recent(self):
        return self.last_finished_time
    most_recent.admin_order_field = 'last_finished_time'
