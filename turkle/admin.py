from bisect import bisect_left
from collections import defaultdict
import csv
from datetime import timedelta
from io import StringIO
import json
import logging
import statistics

from djaa_list_filter2.admin import AjaxAutocompleteListFilterModelAdmin

from django.contrib import admin, messages
from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import DurationField, ExpressionWrapper, F
from django.forms import (FileField, FileInput, HiddenInput, IntegerField, Media,
                          ModelForm, ModelMultipleChoiceField, TextInput, ValidationError, Widget)
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.utils.translation import ngettext
from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import (assign_perm, get_groups_with_perms, get_users_with_perms,
                                remove_perm)
import humanfriendly

from .models import ActiveUser, ActiveProject, Batch, Project, TaskAssignment
from .utils import are_anonymous_tasks_allowed, get_turkle_template_limit

User = get_user_model()

logger = logging.getLogger(__name__)


def _format_timespan(sec):
    return '{} ({:,}s)'.format(humanfriendly.format_timespan(sec, max_units=6), sec)


class UserFullnameMultipleChoiceField(ModelMultipleChoiceField):
    """MultipleChoiceField that displays User's username and full name
    """
    def label_from_instance(self, user):
        return '%s (%s)' % (user.get_full_name(), user.username)


class CustomGroupAdminForm(ModelForm):
    """Hides 'Permissions' section, adds 'Group Members' section
    """
    users = UserFullnameMultipleChoiceField(
        label='Group Members',
        queryset=User.objects.order_by('last_name'),
        required=False,
        widget=FilteredSelectMultiple('User', False),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['users'].initial = self.instance.user_set.all()


class CustomGroupAdmin(GroupAdmin):
    """Hides 'Permissions' section, adds 'Group Members' section
    """
    # We have to use custom logic to add a Users widget to GroupAdmin
    # that is not required when adding a Groups widget to UserAdmin.
    #
    # There is a ManyToMany relationship between Users and Groups, but
    # Django does not treat the two halves of a ManyToManyField
    # identically.  The relationship between the two models is
    # declared in just one of the models, e.g.:
    #
    #   class User(models.Model):
    #       groups = models.ManyToManyField(Group, related_name='user_set')
    #
    # This creates a "forward" relationship from User to Group, and a
    # "reverse" relationship from Group to User.
    #
    # ModelForm behaves very differently for the forward vs. reverse
    # halves of a ManyToManyField relationship.  The default Django
    # UserAdmin just lists 'groups' as one of the fields, and
    # ModelForm renders a FilterSelect widget showing all available
    # Groups.  But if we try to use 'user_set' as one of the fields
    # for GroupAdmin, Django raises a FieldError exception with the
    # message "Unknown field(s) (user_set)".  From Django's
    # perspective, 'groups' is a field of User, but 'user_set' is not
    # a field of Group.

    fields = ('name', 'users')
    form = CustomGroupAdminForm
    list_display = ('name', 'total_members')
    search_fields = ['name']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if 'users' in form.data:
            existing_users = set(obj.user_set.all())
            form_users = set(form.cleaned_data['users'])
            users_to_add = form_users.difference(existing_users)
            users_to_remove = existing_users.difference(form_users)
            for user in users_to_add:
                obj.user_set.add(user)
            for user in users_to_remove:
                obj.user_set.remove(user)
        else:
            obj.user_set.clear()

    def total_members(self, obj):
        return obj.user_set.count()


class CustomUserAdmin(UserAdmin, AjaxAutocompleteListFilterModelAdmin):
    actions = ['activate_users', 'deactivate_users']
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active',
                    'stats')
    autocomplete_list_filter = ('groups',)

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, ngettext(
            '%d user was activated.',
            '%d users were activated.',
            updated,
        ) % updated, messages.SUCCESS)
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        # do not deactivate the logged in user nor the anonymous user object
        queryset = queryset.exclude(username="AnonymousUser")
        queryset = queryset.exclude(username=request.user.username)
        updated = queryset.update(is_active=False)
        self.message_user(request, ngettext(
            '%d user was deactivated.',
            '%d users were deactivated.',
            updated,
        ) % updated, messages.SUCCESS)
    deactivate_users.short_description = "Deactivate selected users"

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            permission_fields = (
                'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        else:
            permission_fields = (
                'is_active', 'is_staff', 'groups')

        if not obj:
            # Adding
            return (
                (None, {'fields': ('username', 'password1', 'password2')}),
                ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
                ('Permissions', {'fields': permission_fields}))
        else:
            # Changing
            return (
                (None, {'fields': ('username', 'password')}),
                ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
                ('Permissions', {'fields': permission_fields}),
                ('Important dates', {'fields': ('last_login', 'date_joined')}))

    def get_readonly_fields(self, request, obj=None):
        return ('last_login', 'date_joined')

    def response_add(self, request, obj, post_url_continue=None):
        # if user clicks save, send to list of users rather than edit screen
        if '_save' in request.POST:
            return redirect(reverse('admin:auth_user_changelist'))
        return super().response_add(request, obj, post_url_continue)

    def stats(self, obj):
        stats_url = reverse('stats_for_user', kwargs={'user_id': obj.id})
        return format_html('<a href="{}" class="button">Stats</a>'.
                           format(stats_url))


class CustomButtonFileWidget(FileInput):
    # HTML file inputs have a button followed by text that either
    # gives the filename or says "no file selected".  It is not
    # possible to modify that text using JavaScript.
    #
    # This template Hides the file input, creates a "Choose File"
    # button (linked to the hidden file input) followed by a span for
    # displaying custom text.
    template_name = "admin/forms/widgets/custom_button_file_widget.html"


class ProjectNameReadOnlyWidget(Widget):
    """Widget displays a link to Project.  Hidden form variable stores Project ID.
    """
    input_type = None

    def __init__(self, project, attrs=None):
        self.project_id = project.id
        self.project_name = project.name
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        return format_html(
            '<div class="readonly"><a href="{}">{}</a></div>'
            '<input name="project" id="id_project" type="hidden" value="{}" />'.format(
                reverse('admin:turkle_project_change', args=[self.project_id]),
                self.project_name, self.project_id))


class BatchForm(ModelForm):
    csv_file = FileField(label='CSV File')

    # Allow a form to be submitted without an 'allotted_assignment_time'
    # field.  The default value for this field will be used instead.
    # See also the function clean_allotted_assignment_time().
    allotted_assignment_time = IntegerField(
        initial=Batch._meta.get_field('allotted_assignment_time').get_default(),
        required=False)

    can_work_on_groups = ModelMultipleChoiceField(
        label='Groups that can work on this Batch',
        queryset=Group.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('Worker Groups', False),
    )
    can_work_on_users = UserFullnameMultipleChoiceField(
        label='Users that can work on this Batch',
        queryset=User.objects.order_by('first_name', 'last_name')
                             .exclude(username='AnonymousUser'),
        required=False,
        widget=FilteredSelectMultiple('Worker Users', False),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['allotted_assignment_time'].label = 'Allotted Assignment Time (hours)'
        self.fields['allotted_assignment_time'].help_text = 'If a user abandons a Task, ' + \
            'this determines how long it takes until their assignment is deleted and ' + \
            'someone else can work on the Task.'
        self.fields['csv_file'].help_text = 'You can Drag-and-Drop a CSV file onto this ' + \
            'window, or use the "Choose File" button to browse for the file'
        self.fields['csv_file'].widget = CustomButtonFileWidget(attrs={
            'class': 'hidden',
            'data-parsley-errors-container': '#file-upload-error',
        })
        self.fields['custom_permissions'].label = 'Restrict access to specific Groups and/or Users'
        self.fields['project'].label = 'Project'
        self.fields['name'].label = 'Batch Name'

        self.fields['active'].help_text = 'Workers can only access a Batch if both the Batch ' + \
            'itself and the associated Project are Active.'

        if not are_anonymous_tasks_allowed():
            # default value of login_required is True
            self.fields['login_required'].widget = HiddenInput()

        if self.instance._state.adding and 'project' in self.initial:
            # We are adding a new Batch where the associated Project has been specified.
            # Per Django convention, the project ID is specified in the URL, e.g.:
            #   /admin/turkle/batch/add/?project=94

            project = Project.objects.get(id=int(self.initial['project']))

            if 'allotted_assignment_time' not in self.initial:
                self.fields['allotted_assignment_time'].initial = project.allotted_assignment_time
            if 'assignments_per_task' not in self.initial:
                self.fields['assignments_per_task'].initial = project.assignments_per_task

            # Pre-populate permissions using permissions from the associated Project
            #
            # The permisisons that are initialized here should match the fields copied
            # over by the batch.copy_project_permissions() function.
            if 'login_required' not in self.initial:
                self.fields['login_required'].initial = project.login_required
            if 'custom_permissions' not in self.initial:
                self.fields['custom_permissions'].initial = project.custom_permissions

            # Pre-populate lists of Groups/Users with permissions for associated Project
            initial_group_ids = [
                str(id)
                for id in get_groups_with_perms(project).values_list('id', flat=True)]
            initial_user_ids = [
                str(id)
                for id in get_users_with_perms(project, with_group_users=False).
                values_list('id', flat=True)]
        else:
            # Pre-populate lists of Groups/Users with permissions for this Batch
            # (Lists will be empty when Adding, but can be non-empty when Changing)
            initial_group_ids = [
                str(id)
                for id in get_groups_with_perms(self.instance).values_list('id', flat=True)]
            initial_user_ids = [
                str(id)
                for id in get_users_with_perms(self.instance, with_group_users=False).
                values_list('id', flat=True)]
        self.fields['can_work_on_groups'].initial = initial_group_ids
        self.fields['can_work_on_users'].initial = initial_user_ids

        # csv_file field not required if changing existing Batch
        #
        # When changing a Batch, the BatchAdmin.get_fields()
        # function will cause the form to be rendered without
        # displaying an HTML form field for the csv_file field.  I was
        # running into strange behavior where Django would still try
        # to validate the csv_file form field, even though there was
        # no way for the user to provide a value for this field.  The
        # two lines below prevent this problem from occurring, by
        # making the csv_file field optional when changing
        # a Batch.
        if not self.instance._state.adding:
            self.fields['csv_file'].required = False
            self.fields['project'].widget = \
                ProjectNameReadOnlyWidget(self.instance.project)

    def clean(self):
        """Verify format of CSV file

        Verify that:
        - fieldnames in CSV file are identical to fieldnames in Project
        - number of fields in each row matches number of fields in CSV header
        """
        cleaned_data = super().clean()

        csv_file = cleaned_data.get("csv_file", False)
        project = cleaned_data.get("project")

        if not csv_file or not project:
            return

        validation_errors = []

        # django InMemoryUploadedFile returns bytes and we need strings
        rows = csv.reader(StringIO(csv_file.read().decode('utf-8')))
        header = next(rows)

        csv_fields = set(header)
        template_fields = set(project.fieldnames)
        if csv_fields != template_fields:
            template_but_not_csv = template_fields.difference(csv_fields)
            if template_but_not_csv:
                validation_errors.append(
                    ValidationError(
                        'The CSV file is missing fields that are in the HTML template. '
                        'These missing fields are: %s' %
                        ', '.join(template_but_not_csv)))

        expected_fields = len(header)
        for (i, row) in enumerate(rows):
            if len(row) != expected_fields:
                validation_errors.append(
                    ValidationError(
                        'The CSV file header has %d fields, but line %d has %d fields' %
                        (expected_fields, i+2, len(row))))

        if validation_errors:
            raise ValidationError(validation_errors)

        # Rewind file, so it can be re-read
        csv_file.seek(0)

    def clean_allotted_assignment_time(self):
        """Clean 'allotted_assignment_time' form field

        - If the allotted_assignment_time field is not submitted as part
          of the form data (e.g. when interacting with this form via a
          script), use the default value.
        - If the allotted_assignment_time is an empty string (e.g. when
          submitting the form using a browser), raise a ValidationError
        """
        data = self.data.get('allotted_assignment_time')
        if data is None:
            return Batch._meta.get_field('allotted_assignment_time').get_default()
        elif data.strip() == '':
            raise ValidationError('This field is required.')
        else:
            return data


def activate_batches(modeladmin, request, queryset):
    queryset.update(active=True)


activate_batches.short_description = "Activate selected Batches"


def activate_projects(modeladmin, request, queryset):
    queryset.update(active=True)


activate_projects.short_description = "Activate selected Projects"


def deactivate_batches(modeladmin, request, queryset):
    queryset.update(active=False)


deactivate_batches.short_description = "Deactivate selected Batches"


def deactivate_projects(modeladmin, request, queryset):
    queryset.update(active=False)


deactivate_projects.short_description = "Deactivate selected Projects"


class BatchAdmin(AjaxAutocompleteListFilterModelAdmin):
    actions = [activate_batches, deactivate_batches]
    form = BatchForm
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '60'})},
    }
    list_display = (
        'name', 'project', 'is_active', 'assignments_completed',
        'stats', 'download_input', 'download_csv',
        )
    list_filter = ('active', 'completed')
    autocomplete_list_filter = ('project', 'created_by',)
    search_fields = ['name']
    autocomplete_fields = ['project']

    class Media:
        css = {
            'all': ('turkle/css/admin-turkle.css',),
        }

    def assignments_completed(self, obj):
        tfa = obj.total_finished_task_assignments()
        ta = obj.assignments_per_task * obj.total_tasks()
        h = format_html(
            '<progress value="{0}" max="{1}" title="Completed {0}/{1} Task Assignments">'
            '</progress> '.format(tfa, ta))
        if tfa >= ta:
            h += _boolean_icon(True)
        else:
            h += format_html('<img src="{}" />', static('admin/img/icon-unknown-alt.svg'))
        h += format_html(' {} / {}'.format(tfa, ta))
        return h

    def activity_json(self, request, batch_id):
        try:
            batch = Batch.objects.get(id=batch_id)
        except ObjectDoesNotExist:
            return JsonResponse({})

        # Create dictionary mapping timestamp (in seconds) to number of TaskAssignments
        # completed at that timestamp
        completed_at = TaskAssignment.objects.\
            filter(completed=True).\
            filter(task__batch=batch).\
            values_list('updated_at', flat=True)
        timestamp_counts = defaultdict(int)
        for ca in completed_at:
            timestamp_counts[int(ca.timestamp())] += 1

        return JsonResponse(timestamp_counts)

    def batch_stats(self, request, batch_id):
        try:
            batch = Batch.objects.get(id=batch_id)
        except ObjectDoesNotExist:
            messages.error(request, 'Cannot find Batch with ID {}'.format(batch_id))
            return redirect(reverse('admin:turkle_batch_changelist'))

        tasks = batch.finished_task_assignments()\
            .annotate(duration=ExpressionWrapper(F('updated_at') - F('created_at'),
                                                 output_field=DurationField()))\
            .order_by('updated_at')\
            .values('assigned_to',  'duration', 'updated_at')

        tasks_updated_at = [t['updated_at'] for t in tasks]
        tasks_duration = [t['duration'].total_seconds() for t in tasks]
        task_duration_by_user = defaultdict(list)
        task_updated_at_by_user = defaultdict(list)
        for t in tasks:
            duration = t['duration'].total_seconds()
            task_duration_by_user[t['assigned_to']].append(duration)
            task_updated_at_by_user[t['assigned_to']].append(t['updated_at'])

        user_ids = task_duration_by_user.keys()
        stats_users = []
        for user in User.objects.filter(id__in=user_ids).order_by('username'):
            has_completed_assignments = user.id in task_duration_by_user
            if has_completed_assignments:
                last_finished_time = task_updated_at_by_user[user.id][-1]
                mean_work_time = int(statistics.mean(task_duration_by_user[user.id]))
                median_work_time = int(statistics.median(task_duration_by_user[user.id]))
            else:
                last_finished_time = 'N/A'
                mean_work_time = 'N/A'
                median_work_time = 'N/A'
            stats_users.append({
                'username': user.username,
                'full_name': user.get_full_name(),
                'has_completed_assignments': has_completed_assignments,
                'assignments_completed': len(task_duration_by_user[user.id]),
                'mean_work_time': mean_work_time,
                'median_work_time': median_work_time,
                'last_finished_time': last_finished_time,
            })

        if tasks:
            first_finished_time = tasks_updated_at[0]
            last_finished_time = tasks_updated_at[-1]
            total_work_time = _format_timespan(int(sum(tasks_duration)))
            mean_work_time = _format_timespan(int(statistics.mean(tasks_duration)))
            median_work_time = _format_timespan(int(statistics.median(tasks_duration)))
        else:
            first_finished_time = 'N/A'
            last_finished_time = 'N/A'
            total_work_time = 'N/A'
            mean_work_time = 'N/A'
            median_work_time = 'N/A'

        context = admin.site.each_context(request)
        context['title'] = f'Stats for Batch: {batch.name}'

        context.update({
            'batch': batch,
            'batch_total_work_time': total_work_time,
            'batch_mean_work_time': mean_work_time,
            'batch_median_work_time': median_work_time,
            'first_finished_time': first_finished_time,
            'last_finished_time': last_finished_time,
            'unsubmitted_task_assignments': batch.unfinished_task_assignments(),
            'stats_users': stats_users,
        })

        return render(request, 'admin/turkle/batch_stats.html', context)

    def cancel_batch(self, request, batch_id):
        try:
            batch = Batch.objects.get(id=batch_id)
            logger.info("User(%i) deleting Batch(%i) %s", request.user.id, batch.id, batch.name)
            batch.delete()
        except ObjectDoesNotExist:
            messages.error(request, 'Cannot find Batch with ID {}'.format(batch_id))

        return redirect(reverse('admin:turkle_batch_changelist'))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            extra_context['published'] = Batch.objects.get(id=object_id).published
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def changelist_view(self, request, extra_context=None):
        c = {
            'csv_unix_line_endings': request.session.get('csv_unix_line_endings', False)
        }
        return super().changelist_view(request, extra_context=c)

    def download_csv(self, obj):
        download_url = reverse('admin:turkle_download_batch', kwargs={'batch_id': obj.id})
        return format_html('<a href="{}" class="button">CSV results</a>'.format(download_url))

    def download_input(self, obj):
        download_url = reverse('admin:turkle_download_batch_input', kwargs={'batch_id': obj.id})
        return format_html('<a href="{}" class="button">CSV input</a>'.format(download_url))

    def get_fieldsets(self, request, obj=None):
        # Display different fields when adding (when obj is None) vs changing a Batch
        if not obj:
            # Adding
            return (
                (None, {
                    'fields': ('project', 'name', 'csv_file'),
                }),
                ('Status', {
                    'fields': ('active',)
                }),
                ('Task Assignment Settings', {
                    'fields': ('assignments_per_task', 'allotted_assignment_time')
                }),
                ('Permissions', {
                    'fields': (
                        'login_required', 'custom_permissions',
                        'can_work_on_groups', 'can_work_on_users'
                    )
                }),
            )
        else:
            # Changing
            return (
                (None, {
                    'fields': ('project', 'name', 'filename')
                }),
                ('Status', {
                    'fields': ('active', 'published')
                }),
                ('Task Assignment Settings', {
                    'fields': ('assignments_per_task', 'allotted_assignment_time')
                }),
                ('Permissions', {
                    'fields': (
                        'login_required', 'custom_permissions',
                        'can_work_on_groups', 'can_work_on_users'
                    )
                }),
            )

    def get_list_display_links(self, request, list_display):
        if request.user.has_perm('turkle.change_batch'):
            return ('name',)
        else:
            return (None,)

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return []
        else:
            return ('assignments_per_task', 'filename', 'published')

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<int:batch_id>/cancel/',
                 self.admin_site.admin_view(self.cancel_batch), name='turkle_cancel_batch'),
            path('<int:batch_id>/review/',
                 self.admin_site.admin_view(self.review_batch), name='turkle_review_batch'),
            path('<int:batch_id>/publish/',
                 self.admin_site.admin_view(self.publish_batch), name='turkle_publish_batch'),
            path('<int:batch_id>/download/',
                 self.admin_site.admin_view(self.download_batch), name='turkle_download_batch'),
            path('<int:batch_id>/input/',
                 self.admin_site.admin_view(self.download_batch_input),
                 name='turkle_download_batch_input'),
            path('<int:batch_id>/activity.json',
                 self.admin_site.admin_view(self.activity_json),
                 name='turkle_batch_activity_json'),
            path('<int:batch_id>/stats/',
                 self.admin_site.admin_view(self.batch_stats), name='turkle_batch_stats'),
            path('update_csv_line_endings',
                 self.admin_site.admin_view(self.update_csv_line_endings),
                 name='turkle_update_csv_line_endings'),
        ]
        return my_urls + urls

    def publish_batch(self, request, batch_id):
        try:
            batch = Batch.objects.get(id=batch_id)
            batch.published = True
            batch.save()
            logger.info("User(%i) publishing Batch(%i) %s", request.user.id, batch.id, batch.name)
        except ObjectDoesNotExist:
            messages.error(request, 'Cannot find Batch with ID {}'.format(batch_id))

        return redirect(reverse('admin:turkle_batch_changelist'))

    def download_batch(self, request, batch_id):
        batch = Batch.objects.get(id=batch_id)
        csv_output = StringIO()
        if request.session.get('csv_unix_line_endings', False):
            batch.to_csv(csv_output, lineterminator='\n')
        else:
            batch.to_csv(csv_output)
        csv_string = csv_output.getvalue()
        response = HttpResponse(csv_string, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            batch.csv_results_filename())
        return response

    def download_batch_input(self, request, batch_id):
        batch = Batch.objects.get(id=batch_id)
        csv_output = StringIO()
        if request.session.get('csv_unix_line_endings', False):
            batch.to_input_csv(csv_output, lineterminator='\n')
        else:
            batch.to_input_csv(csv_output)
        csv_string = csv_output.getvalue()
        response = HttpResponse(csv_string, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            batch.filename)
        return response

    def response_add(self, request, obj, post_url_continue=None):
        return redirect(reverse('admin:turkle_review_batch', kwargs={'batch_id': obj.id}))

    def response_change(self, request, obj):
        # catch unpublished batch when saved to redirect to review page
        if not obj.published:
            return redirect(reverse('admin:turkle_review_batch', kwargs={'batch_id': obj.id}))
        return super().response_change(request, obj)

    def review_batch(self, request, batch_id):
        request.current_app = self.admin_site.name
        try:
            batch = Batch.objects.get(id=batch_id)
        except ObjectDoesNotExist:
            messages.error(request, 'Cannot find Batch with ID {}'.format(batch_id))
            return redirect(reverse('admin:turkle_batch_changelist'))

        task_ids = list(batch.task_set.values_list('id', flat=True))
        task_ids_as_json = json.dumps(task_ids)
        return render(request, 'admin/turkle/review_batch.html', {
            'batch_id': batch_id,
            'first_task_id': task_ids[0],
            'task_ids_as_json': task_ids_as_json,
            'site_header': self.admin_site.site_header,
            'site_title': self.admin_site.site_title,
            'title': 'Review Batch',
            'media': Media(self.Media),
            # below is for the breadcrumbs
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request, batch),
        })

    def save_model(self, request, obj, form, change):
        if obj._state.adding:
            if request.user.is_authenticated:
                obj.created_by = request.user

            # When creating a new batch, set published flag as false until reviewed
            obj.published = False

            # Only use CSV file when adding Batch, not when changing
            obj.filename = request.FILES['csv_file']._name
            csv_text = request.FILES['csv_file'].read()
            super().save_model(request, obj, form, change)
            logger.info("User(%i) creating Batch(%i) %s", request.user.id, obj.id, obj.name)

            csv_fh = StringIO(csv_text.decode('utf-8'))
            csv_fields = set(next(csv.reader(csv_fh)))
            csv_fh.seek(0)

            template_fields = set(obj.project.fieldnames)
            if csv_fields != template_fields:
                csv_but_not_template = csv_fields.difference(template_fields)
                if csv_but_not_template:
                    messages.warning(
                        request,
                        'The CSV file contained fields that are not in the HTML template. '
                        'These extra fields are: %s' %
                        ', '.join(csv_but_not_template))
            obj.create_tasks_from_csv(csv_fh)
        else:
            super().save_model(request, obj, form, change)
            logger.info("User(%i) updating Batch(%i) %s", request.user.id, obj.id, obj.name)

        if 'can_work_on_groups' in form.data:
            existing_groups = set(get_groups_with_perms(obj))
            form_groups = set(form.cleaned_data['can_work_on_groups'])
            groups_to_add = form_groups.difference(existing_groups)
            groups_to_remove = existing_groups.difference(form_groups)
            for group in groups_to_add:
                assign_perm('can_work_on_batch', group, obj)
            for group in groups_to_remove:
                remove_perm('can_work_on_batch', group, obj)
        else:
            for group in get_groups_with_perms(obj):
                remove_perm('can_work_on_batch', group, obj)
        if 'can_work_on_users' in form.data:
            existing_users = set(get_users_with_perms(obj, with_group_users=False))
            form_users = set(form.cleaned_data['can_work_on_users'])
            users_to_add = form_users.difference(existing_users)
            users_to_remove = existing_users.difference(form_users)
            for user in users_to_add:
                assign_perm('can_work_on_batch', user, obj)
            for user in users_to_remove:
                remove_perm('can_work_on_batch', user, obj)
        else:
            for user in get_users_with_perms(obj, with_group_users=False):
                remove_perm('can_work_on_batch', user, obj)

    def stats(self, obj):
        stats_url = reverse('admin:turkle_batch_stats', kwargs={'batch_id': obj.id})
        return format_html('<a href="{}" class="button">Stats</a>'.
                           format(stats_url))

    def update_csv_line_endings(self, request):
        csv_unix_line_endings = (request.POST['csv_unix_line_endings'] == 'true')
        request.session['csv_unix_line_endings'] = csv_unix_line_endings
        return JsonResponse({})


class ProjectForm(ModelForm):
    # Allow a form to be submitted without an 'allotted_assignment_time'
    # field.  The default value for this field will be used instead.
    # See also the function clean_allotted_assignment_time().
    allotted_assignment_time = IntegerField(
        initial=Project._meta.get_field('allotted_assignment_time').get_default(),
        required=False)

    template_file_upload = FileField(label='HTML template file', required=False)
    can_work_on_groups = ModelMultipleChoiceField(
        label='Groups that can work on this Project',
        queryset=Group.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('Worker Groups', False),
    )
    can_work_on_users = UserFullnameMultipleChoiceField(
        label='Users that can work on this Project',
        queryset=User.objects.order_by('first_name', 'last_name')
                             .exclude(username='AnonymousUser'),
        required=False,
        widget=FilteredSelectMultiple('Worker Users', False),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['template_file_upload'].widget = CustomButtonFileWidget(attrs={
            'class': 'hidden',
        })

        # This hidden form field is updated by JavaScript code in the
        # customized admin template file:
        #   turkle/templates/admin/turkle/project/change_form.html
        self.fields['filename'].widget = HiddenInput()

        if not are_anonymous_tasks_allowed():
            # default value of login_required is True
            self.fields['login_required'].widget = HiddenInput()

        self.fields['allotted_assignment_time'].label = 'Allotted Assignment Time (hours)'
        self.fields['allotted_assignment_time'].help_text = 'If a user abandons a Task, ' + \
            'this determines how long it takes until their assignment is deleted and ' + \
            'someone else can work on the Task. ' + \
            'Changing this parameter DOES NOT change the Allotted Assignment Time for already ' + \
            'published Batches of Tasks.'
        self.fields['assignments_per_task'].label = 'Assignments per Task'
        self.fields['assignments_per_task'].help_text = 'Changing this ' + \
            'parameter DOES NOT change the number of Assignments per Task for already ' + \
            'published Batches of Tasks.'
        self.fields['custom_permissions'].label = 'Restrict access to specific Groups and/or Users'
        self.fields['html_template'].label = 'HTML template text'
        limit = str(get_turkle_template_limit())
        self.fields['html_template'].help_text = 'You can edit the template text directly, ' + \
            'Drag-and-Drop a template file onto this window, ' + \
            'or use the "Choose File" button below. Maximum size is ' + limit + ' KB.'
        byte_limit = str(get_turkle_template_limit(True))
        self.fields['html_template'].widget.attrs['data-parsley-maxlength'] = byte_limit
        self.fields['html_template'].widget.attrs['data-parsley-group'] = 'html_template'

        self.fields['active'].help_text = 'Deactivating a Project effectively deactivates ' + \
            'all associated Batches.  Workers can only access a Batch if both the Batch ' + \
            'itself and the associated Project are Active.'

        initial_group_ids = [
            str(id)
            for id in get_groups_with_perms(self.instance).values_list('id', flat=True)]
        self.fields['can_work_on_groups'].initial = initial_group_ids

        initial_user_ids = [
            str(id)
            for id in get_users_with_perms(self.instance, with_group_users=False).
            values_list('id', flat=True)]
        self.fields['can_work_on_users'].initial = initial_user_ids

    def clean_allotted_assignment_time(self):
        """Clean 'allotted_assignment_time' form field

        - If the allotted_assignment_time field is not submitted as part
          of the form data (e.g. when interacting with this form via a
          script), use the default value.
        - If the allotted_assignment_time is an empty string (e.g. when
          submitting the form using a browser), raise a ValidationError
        """
        data = self.data.get('allotted_assignment_time')
        if data is None:
            return Project._meta.get_field('allotted_assignment_time').get_default()
        elif data.strip() == '':
            raise ValidationError('This field is required.')
        else:
            return data


class ProjectAdmin(GuardedModelAdmin, AjaxAutocompleteListFilterModelAdmin):
    actions = [activate_projects, deactivate_projects]
    change_form_template = 'admin/turkle/project/change_form.html'
    form = ProjectForm
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '60'})},
    }
    list_filter = ('active',)
    autocomplete_list_filter = ('created_by',)
    search_fields = ['name']

    # Fieldnames are extracted from form text, and should not be edited directly
    exclude = ('fieldnames',)
    readonly_fields = ('extracted_template_variables',)

    class Media:
        css = {
            'all': ('turkle/css/admin-turkle.css',),
        }

    def activity_json(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except ObjectDoesNotExist:
            return JsonResponse({})

        # Create dictionary mapping timestamp (in seconds) to number of TaskAssignments
        # completed at that timestamp
        completed_at = TaskAssignment.objects.\
            filter(completed=True).\
            filter(task__batch__project=project).\
            values_list('updated_at', flat=True)
        timestamp_counts = defaultdict(int)
        for ca in completed_at:
            timestamp_counts[int(ca.timestamp())] += 1

        return JsonResponse(timestamp_counts)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<int:project_id>/activity.json',
                 self.admin_site.admin_view(self.activity_json),
                 name='turkle_project_activity_json'),
            path('<int:project_id>/stats/',
                 self.admin_site.admin_view(self.project_stats), name='turkle_project_stats'),
            # backward compatibility for active-projects and active-users.
            path('active-projects/',
                 lambda x: redirect(reverse('admin:turkle_activeproject_changelist'))),
            path('active-users/',
                 lambda x: redirect(reverse('admin:turkle_activeuser_changelist'))),
        ]
        return my_urls + urls

    def extracted_template_variables(self, instance):
        return format_html_join('\n', "<li>{}</li>",
                                ((f, ) for f in instance.fieldnames.keys()))

    def get_fieldsets(self, request, obj=None):
        if not obj:
            # Adding
            return (
                (None, {
                    'fields': ('name',)
                }),
                ('HTML Template', {
                    'fields': ('html_template', 'template_file_upload', 'filename')
                }),
                ('Status', {
                    'fields': ('active',)
                }),
                ('Default Task Assignment Settings for new Batches', {
                    'fields': ('assignments_per_task', 'allotted_assignment_time')
                }),
                ('Default Permissions for new Batches', {
                    'fields': (
                        'login_required', 'custom_permissions',
                        'can_work_on_groups', 'can_work_on_users'
                    )
                }),
            )
        else:
            # Changing
            return (
                (None, {
                    'fields': ('name',)
                }),
                ('HTML Template', {
                    'fields': ('html_template', 'template_file_upload', 'filename',
                               'extracted_template_variables')
                }),
                ('Status', {
                    'fields': ('active',)
                }),
                ('Default Task Assignment Settings for new Batches', {
                    'fields': ('assignments_per_task', 'allotted_assignment_time')
                }),
                ('Default Permissions for new Batches', {
                    'fields': (
                        'login_required', 'custom_permissions',
                        'can_work_on_groups', 'can_work_on_users'
                    )
                }),
            )

    def get_list_display(self, request):
        if request.user.has_perm('turkle.add_batch'):
            return ('name', 'filename', 'updated_at', 'active', 'stats', 'publish_tasks')
        else:
            return ('name', 'filename', 'updated_at', 'active', 'stats')

    def get_list_display_links(self, request, list_display):
        if request.user.has_perm('turkle.change_project'):
            return ('name',)
        else:
            return (None,)

    def project_stats(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except ObjectDoesNotExist:
            messages.error(request, 'Cannot find Project with ID {}'.format(project_id))
            return redirect(reverse('admin:turkle_project_changelist'))

        tasks = project.finished_task_assignments()\
            .annotate(duration=ExpressionWrapper(F('updated_at') - F('created_at'),
                                                 output_field=DurationField()))\
            .order_by('updated_at')\
            .values('assigned_to', 'task__batch_id', 'duration', 'updated_at')

        tasks_updated_at = [t['updated_at'] for t in tasks]
        tasks_duration = [t['duration'].total_seconds() for t in tasks]
        task_duration_by_batch = defaultdict(list)
        task_updated_at_by_batch = defaultdict(list)
        task_duration_by_user = defaultdict(list)
        task_updated_at_by_user = defaultdict(list)
        for t in tasks:
            duration = t['duration'].total_seconds()
            task_duration_by_batch[t['task__batch_id']].append(duration)
            task_updated_at_by_batch[t['task__batch_id']].append(t['updated_at'])
            task_duration_by_user[t['assigned_to']].append(duration)
            task_updated_at_by_user[t['assigned_to']].append(t['updated_at'])

        uncompleted_tas_active_batches = 0
        uncompleted_tas_inactive_batches = 0

        stats_batches = []
        for batch in project.batch_set.order_by('name'):
            has_completed_assignments = batch.id in task_duration_by_batch
            if has_completed_assignments:
                assignments_completed = len(task_duration_by_batch[batch.id])
                last_finished_time = task_updated_at_by_batch[batch.id][-1]
                mean_work_time = int(statistics.mean(task_duration_by_batch[batch.id]))
                median_work_time = int(statistics.median(task_duration_by_batch[batch.id]))
            else:
                assignments_completed = 0
                last_finished_time = 'N/A'
                mean_work_time = 'N/A'
                median_work_time = 'N/A'
            total_task_assignments = batch.total_task_assignments()
            if total_task_assignments != 0:
                assignments_completed_percentage = '%.1f' % \
                    (100.0 * assignments_completed / total_task_assignments)
            else:
                assignments_completed_percentage = 'N/A'
            stats_batches.append({
                'batch_id': batch.id,
                'name': batch.name,
                'active': batch.active,
                'has_completed_assignments': has_completed_assignments,
                'assignments_completed': assignments_completed,
                'total_task_assignments': total_task_assignments,
                'assignments_completed_percentage': assignments_completed_percentage,
                'mean_work_time': mean_work_time,
                'median_work_time': median_work_time,
                'last_finished_time': last_finished_time,
            })

            # We use max(0, x) to ensure the # of remaining Task
            # Assignments for each Batch is never negative.
            #
            # In theory, the number of completed Task Assignments
            # should never exceed the number of Task Assignments
            # computed by Batch.total_task_assignments() - but in
            # practice, this has happened due to a race condition.
            if batch.active:
                uncompleted_tas_active_batches += \
                    max(0, total_task_assignments - assignments_completed)
            else:
                uncompleted_tas_inactive_batches += \
                    max(0, total_task_assignments - assignments_completed)

        user_ids = task_duration_by_user.keys()
        stats_users = []
        for user in User.objects.filter(id__in=user_ids).order_by('username'):
            has_completed_assignments = user.id in task_duration_by_user
            if has_completed_assignments:
                last_finished_time = task_updated_at_by_user[user.id][-1]
                mean_work_time = int(statistics.mean(task_duration_by_user[user.id]))
                median_work_time = int(statistics.median(task_duration_by_user[user.id]))
            else:
                last_finished_time = 'N/A'
                mean_work_time = 'N/A'
                median_work_time = 'N/A'
            stats_users.append({
                'username': user.username,
                'full_name': user.get_full_name(),
                'has_completed_assignments': has_completed_assignments,
                'assignments_completed': len(task_duration_by_user[user.id]),
                'mean_work_time': mean_work_time,
                'median_work_time': median_work_time,
                'last_finished_time': last_finished_time,
            })

        if tasks:
            now = timezone.now()
            tca_1_day = len(tasks) - bisect_left(tasks_updated_at, now - timedelta(days=1))
            tca_7_day = len(tasks) - bisect_left(tasks_updated_at, now - timedelta(days=7))
            tca_30_day = len(tasks) - bisect_left(tasks_updated_at, now - timedelta(days=30))
            tca_90_day = len(tasks) - bisect_left(tasks_updated_at, now - timedelta(days=90))
            tca_180_day = len(tasks) - bisect_left(tasks_updated_at, now - timedelta(days=180))
            tca_365_day = len(tasks) - bisect_left(tasks_updated_at, now - timedelta(days=365))
            first_finished_time = tasks_updated_at[0]
            last_finished_time = tasks_updated_at[-1]
            total_work_time = _format_timespan(int(sum(tasks_duration)))
            mean_work_time = _format_timespan(int(statistics.mean(tasks_duration)))
            median_work_time = _format_timespan(int(statistics.median(tasks_duration)))
        else:
            tca_1_day = 'N/A'
            tca_7_day = 'N/A'
            tca_30_day = 'N/A'
            tca_90_day = 'N/A'
            tca_180_day = 'N/A'
            tca_365_day = 'N/A'
            first_finished_time = 'N/A'
            last_finished_time = 'N/A'
            total_work_time = 'N/A'
            mean_work_time = 'N/A'
            median_work_time = 'N/A'

        context = admin.site.each_context(request)
        context['title'] = f'Stats for Project: {project.name}'

        context.update({
            'project': project,
            'project_total_completed_assignments': len(tasks),
            'project_total_completed_assignments_1_day': tca_1_day,
            'project_total_completed_assignments_7_day': tca_7_day,
            'project_total_completed_assignments_30_day': tca_30_day,
            'project_total_completed_assignments_90_day': tca_90_day,
            'project_total_completed_assignments_180_day': tca_180_day,
            'project_total_completed_assignments_365_day': tca_365_day,
            'project_total_work_time': total_work_time,
            'project_mean_work_time': mean_work_time,
            'project_median_work_time': median_work_time,
            'first_finished_time': first_finished_time,
            'last_finished_time': last_finished_time,
            'stats_users': stats_users,
            'stats_batches': stats_batches,
            'uncompleted_tas_active_batches': uncompleted_tas_active_batches,
            'uncompleted_tas_inactive_batches': uncompleted_tas_inactive_batches,
        })

        return render(request, 'admin/turkle/project_stats.html', context)

    def publish_tasks(self, instance):
        publish_tasks_url = '%s?project=%d' % (
            reverse('admin:turkle_batch_add'),
            instance.id)
        return format_html('<a href="{}" class="button">Publish Tasks</a>'.
                           format(publish_tasks_url))
    publish_tasks.short_description = 'Publish Tasks'

    def save_model(self, request, obj, form, change):
        new_flag = obj._state.adding
        if request.user.is_authenticated:
            obj.updated_by = request.user
            if new_flag:
                obj.created_by = request.user

        super().save_model(request, obj, form, change)
        if new_flag:
            logger.info("User(%i) creating Project(%i) %s", request.user.id, obj.id, obj.name)
        else:
            logger.info("User(%i) updating Project(%i) %s", request.user.id, obj.id, obj.name)

        if 'can_work_on_groups' in form.data:
            existing_groups = set(get_groups_with_perms(obj))
            form_groups = set(form.cleaned_data['can_work_on_groups'])
            groups_to_add = form_groups.difference(existing_groups)
            groups_to_remove = existing_groups.difference(form_groups)
            for group in groups_to_add:
                assign_perm('can_work_on', group, obj)
            for group in groups_to_remove:
                remove_perm('can_work_on', group, obj)
        else:
            for group in get_groups_with_perms(obj):
                remove_perm('can_work_on', group, obj)
        if 'can_work_on_users' in form.data:
            existing_users = set(get_users_with_perms(obj, with_group_users=False))
            form_users = set(form.cleaned_data['can_work_on_users'])
            users_to_add = form_users.difference(existing_users)
            users_to_remove = existing_users.difference(form_users)
            for user in users_to_add:
                assign_perm('can_work_on', user, obj)
            for user in users_to_remove:
                remove_perm('can_work_on', user, obj)
        else:
            for user in get_users_with_perms(obj, with_group_users=False):
                remove_perm('can_work_on', user, obj)

    def delete_model(self, request, obj):
        logger.info("User(%i) deleting Project(%i) %s", request.user.id, obj.id, obj.name)
        super().delete_model(request, obj)

    def stats(self, obj):
        stats_url = reverse('admin:turkle_project_stats', kwargs={'project_id': obj.id})
        return format_html('<a href="{}" class="button">Stats</a>'.
                           format(stats_url))


class ViewOnlyAdminMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class TaskAssignmentAdmin(admin.ModelAdmin):
    """View for assignments to expire abandoned ones"""

    class Media:
        css = {
            'all': ('turkle/css/admin-turkle.css',),
        }

    # this turns off the add button in admin sidebar for task assignments
    def has_add_permission(self, request):
        return False

    def changelist_view(self, request, extra_context=None):
        num_incomplete_tasks = TaskAssignment.objects.\
            filter(completed=False).\
            count()
        num_expired_tasks = TaskAssignment.objects.\
            filter(completed=False).\
            filter(expires_at__lt=timezone.now()).\
            count()
        extra_context = {
            'num_incomplete_tasks': num_incomplete_tasks,
            'num_expired_tasks': num_expired_tasks
        }
        return super().changelist_view(request, extra_context)

    @staticmethod
    def expire_abandoned_assignments(request):
        (total_deleted, _) = TaskAssignment.expire_all_abandoned()
        messages.info(request, 'All {} abandoned Tasks have been expired'.format(total_deleted))
        return redirect(reverse('admin:turkle_taskassignment_changelist'))

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('expire_abandoned_assignments/',
                 self.admin_site.admin_view(self.expire_abandoned_assignments),
                 name='turkle_expire_abandoned_assignments'),
        ]
        return my_urls + urls


class ActiveObjectPeriodListFilter(admin.SimpleListFilter):
    """Filter active objects by period of activity"""
    title = 'active period'
    parameter_name = 'period'
    default_value = '7'

    def lookups(self, request, model_admin):
        return (
            ('1', 'last 1 day'),
            ('2', 'last 2 days'),
            ('7', 'last 7 days'),
            ('30', 'last 30 days'),
        )

    def choices(self, changelist):
        # override to remove 'All' as a choice
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == str(lookup),
                'query_string': changelist.get_query_string({self.parameter_name: lookup}),
                'display': title,
            }

    def value(self):
        # override to provide a default value
        period_value = super().value()
        return period_value if period_value else self.default_value

    def queryset(self, request, queryset):
        # handling of filter value is done in model admin, so return queryset as is
        return queryset


class ActiveUserChangeList(ChangeList):
    def url_for_result(self, result):
        # change URL for active user to point to stats page
        return reverse('stats_for_user', kwargs={'user_id': result.id})


class ActiveUserAdmin(ViewOnlyAdminMixin, admin.ModelAdmin):
    """Active user admin with recency filter.

    ActiveUser is a proxy class for User. Its manager queries based on recent assignments.
    This Admin is view only and customized with a period filter.
    Passing a value to the original queryset is non-standard in Django and must be done
    because of the way we are querying for active users.
    """
    list_display = ('name', 'username', 'completed_assignments', 'most_recent')
    list_filter = (ActiveObjectPeriodListFilter,)
    list_per_page = 20
    preserve_filters = False

    def get_changelist(self, request, **kwargs):
        return ActiveUserChangeList

    def get_queryset(self, request):
        # override to pass n_days from filter directly to manager
        period = request.GET.get(ActiveObjectPeriodListFilter.parameter_name,
                                 ActiveObjectPeriodListFilter.default_value)
        qs = self.model._default_manager.get_queryset(n_days=period)
        # in some future version of Django, this might be handled by the ChangeList
        # see to do comment in django/contrib/admin/options.py
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs


class ActiveProjectChangeList(ChangeList):
    def url_for_result(self, result):
        # change URL for active project to point to stats page
        return reverse('admin:turkle_project_stats', kwargs={'project_id': result.id})


class ActiveProjectAdmin(ViewOnlyAdminMixin, admin.ModelAdmin):
    """Active project admin with recency filter."""
    list_display = ('name', 'created_by', 'completed_assignments', 'most_recent')
    list_filter = (ActiveObjectPeriodListFilter,)
    list_per_page = 20
    preserve_filters = False

    def get_changelist(self, request, **kwargs):
        return ActiveProjectChangeList

    def get_queryset(self, request):
        # override to pass n_days from filter directly to manager
        period = request.GET.get(ActiveObjectPeriodListFilter.parameter_name,
                                 ActiveObjectPeriodListFilter.default_value)
        qs = self.model._default_manager.get_queryset(n_days=period)
        # in some future version of Django, this might be handled by the ChangeList
        # see to do comment in django/contrib/admin/options.py
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs


# replace default Group and User admin with ours
if admin.site.is_registered(Group):
    admin.site.unregister(Group)
if admin.site.is_registered(User):
    admin.site.unregister(User)
admin.site.register(Group, CustomGroupAdmin)
admin.site.register(User, CustomUserAdmin)

admin.site.register(ActiveUser, ActiveUserAdmin)
admin.site.register(ActiveProject, ActiveProjectAdmin)
admin.site.register(Batch, BatchAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(TaskAssignment, TaskAssignmentAdmin)
