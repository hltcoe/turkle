from bisect import bisect_left
from collections import defaultdict
import csv
from datetime import datetime, timedelta, timezone
from io import StringIO
import json
import logging
import statistics

from admin_auto_filters.filters import AutocompleteFilter
from admin_auto_filters.views import AutocompleteJsonView
from django.contrib import admin, messages
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import DurationField, ExpressionWrapper, F
from django.forms import (FileField, FileInput, HiddenInput, IntegerField,
                          ModelForm, ModelMultipleChoiceField, TextInput, ValidationError, Widget)
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join
from django.utils.translation import ngettext
from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import assign_perm, get_groups_with_perms, remove_perm
import humanfriendly

from .models import Batch, Project, TaskAssignment
from .utils import get_site_name, get_turkle_template_limit

logger = logging.getLogger(__name__)


def _format_timespan(sec):
    return '{} ({:,}s)'.format(humanfriendly.format_timespan(sec, max_units=6), sec)


class TurkleAdminSite(admin.AdminSite):
    app_index_template = 'admin/turkle/app_index.html'
    site_header = get_site_name() + ' administration'
    site_title = get_site_name() + ' site admin'

    def expire_abandoned_assignments(self, request):
        (total_deleted, _) = TaskAssignment.expire_all_abandoned()
        messages.info(request, 'All {} abandoned Tasks have been expired'.format(total_deleted))
        return redirect(reverse('turkle_admin:index'))

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('expire_abandoned_assignments/',
                 self.admin_view(self.expire_abandoned_assignments),
                 name='expire_abandoned_assignments'),
        ]
        return my_urls + urls


class CustomGroupMultipleChoiceField(ModelMultipleChoiceField):
    def label_from_instance(self, user):
        return '%s (%s)' % (user.get_full_name(), user.username)


class CustomGroupAdminForm(ModelForm):
    """Hides 'Permissions' section, adds 'Group Members' section
    """
    users = CustomGroupMultipleChoiceField(
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


class GroupFilter(AutocompleteFilter):
    title = 'groups'
    field_name = 'groups'


class CustomUserAdmin(UserAdmin):
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                    'groups')}),
    )
    actions = ['activate_users', 'deactivate_users']
    list_filter = ('is_active', 'is_staff', 'is_superuser', GroupFilter, 'date_joined')
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')

    # required by django-admin-autocomplete-filter 0.5
    class Media:
        pass

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

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('autocomplete-batch-owner',
                 self.admin_site.admin_view(BatchCreatorSearchView.as_view(model_admin=self)),
                 name='autocomplete_batch_owner'),
            path('autocomplete-project-owner',
                 self.admin_site.admin_view(ProjectCreatorSearchView.as_view(model_admin=self)),
                 name='autocomplete_project_owner'),
        ]
        return my_urls + urls

    def response_add(self, request, obj, post_url_continue=None):
        # if user clicks save, send to list of users rather than edit screen
        if '_save' in request.POST:
            return redirect(reverse('turkle_admin:auth_user_changelist'))
        return super().response_add(request, obj, post_url_continue)


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
                reverse('turkle_admin:turkle_project_change', args=[self.project_id]),
                self.project_name, self.project_id))


class BatchForm(ModelForm):
    csv_file = FileField(label='CSV File')

    # Allow a form to be submitted without an 'allotted_assignment_time'
    # field.  The default value for this field will be used instead.
    # See also the function clean_allotted_assignment_time().
    allotted_assignment_time = IntegerField(
        initial=Batch._meta.get_field('allotted_assignment_time').get_default(),
        required=False)

    worker_permissions = ModelMultipleChoiceField(
        label='Worker Groups with access to this Batch',
        queryset=Group.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('Worker Groups', False),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['allotted_assignment_time'].label = 'Allotted assignment time (hours)'
        self.fields['allotted_assignment_time'].help_text = 'If a user abandons a Task, ' + \
            'this determines how long it takes until their assignment is deleted and ' + \
            'someone else can work on the Task.'
        self.fields['csv_file'].help_text = 'You can Drag-and-Drop a CSV file onto this ' + \
            'window, or use the "Choose File" button to browse for the file'
        self.fields['csv_file'].widget = CustomButtonFileWidget(attrs={
            'class': 'hidden',
            'data-parsley-errors-container': '#file-upload-error',
        })
        self.fields['custom_permissions'].label = 'Restrict access to specific Groups of Workers '
        self.fields['project'].label = 'Project'
        self.fields['name'].label = 'Batch Name'

        self.fields['active'].help_text = 'Workers can only access a Batch if both the Batch ' + \
            'itself and the associated Project are Active.'

        if self.instance._state.adding and 'project' in self.initial:
            # We are adding a new Batch where the associated Project has been specified.
            # Per Django convention, the project ID is specified in the URL, e.g.:
            #   /admin/turkle/batch/add/?project=94

            # NOTE: The fields that are initialized here should match the fields copied
            #       over by the batch.copy_project_permissions() function.

            project = Project.objects.get(id=int(self.initial['project']))
            self.fields['custom_permissions'].initial = project.custom_permissions
            self.fields['login_required'].initial = project.login_required

            # Pre-populate permissions using permissions from the associated Project
            initial_ids = [str(id)
                           for id in get_groups_with_perms(project).values_list('id', flat=True)]
        else:
            # Pre-populate permissions
            initial_ids = [str(id)
                           for id in get_groups_with_perms(self.instance).
                           values_list('id', flat=True)]
        self.fields['worker_permissions'].initial = initial_ids

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


class BatchCreatorFilter(AutocompleteFilter):
    title = 'creator'
    field_name = 'created_by'

    def get_autocomplete_url(self, request, model_admin):
        return reverse('turkle_admin:autocomplete_batch_owner')


class BatchCreatorSearchView(AutocompleteJsonView):
    def get_queryset(self):
        return super().get_queryset().exclude(created_batches=None)


class ProjectCreatorFilter(AutocompleteFilter):
    title = 'creator'
    field_name = 'created_by'

    def get_autocomplete_url(self, request, model_admin):
        return reverse('turkle_admin:autocomplete_project_owner')


class ProjectCreatorSearchView(AutocompleteJsonView):
    def get_queryset(self):
        return super().get_queryset().exclude(created_projects=None)


class ProjectFilter(AutocompleteFilter):
    title = 'project'
    field_name = 'project'

    def get_autocomplete_url(self, request, model_admin):
        return reverse('turkle_admin:autocomplete_project_order_by_name')


class ProjectSearchView(AutocompleteJsonView):
    def get_queryset(self):
        return super().get_queryset().order_by('name')


class BatchAdmin(admin.ModelAdmin):
    actions = [activate_batches, deactivate_batches]
    form = BatchForm
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '60'})},
    }
    list_display = (
        'name', 'project', 'is_active', 'assignments_completed',
        'stats', 'download_input', 'download_csv',
        )
    list_filter = ('active', 'completed', BatchCreatorFilter, ProjectFilter)
    search_fields = ['name']
    autocomplete_fields = ['project']

    # required by django-admin-autocomplete-filter 0.5
    class Media:
        pass

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

    def batch_stats(self, request, batch_id):
        try:
            batch = Batch.objects.get(id=batch_id)
        except ObjectDoesNotExist:
            messages.error(request, 'Cannot find Batch with ID {}'.format(batch_id))
            return redirect(reverse('turkle_admin:turkle_batch_changelist'))

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

        return render(request, 'admin/turkle/batch_stats.html', {
            'batch': batch,
            'batch_total_work_time': total_work_time,
            'batch_mean_work_time': mean_work_time,
            'batch_median_work_time': median_work_time,
            'first_finished_time': first_finished_time,
            'last_finished_time': last_finished_time,
            'stats_users': stats_users,
        })

    def cancel_batch(self, request, batch_id):
        try:
            batch = Batch.objects.get(id=batch_id)
            logger.info("User(%i) deleting Batch(%i) %s", request.user.id, batch.id, batch.name)
            batch.delete()
        except ObjectDoesNotExist:
            messages.error(request, 'Cannot find Batch with ID {}'.format(batch_id))

        return redirect(reverse('turkle_admin:turkle_batch_changelist'))

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
        download_url = reverse('turkle_admin:download_batch', kwargs={'batch_id': obj.id})
        return format_html('<a href="{}" class="button">CSV results</a>'.format(download_url))

    def download_input(self, obj):
        download_url = reverse('turkle_admin:download_batch_input', kwargs={'batch_id': obj.id})
        return format_html('<a href="{}" class="button">CSV input</a>'.format(download_url))

    def get_fieldsets(self, request, obj=None):
        # Display different fields when adding (when obj is None) vs changing a Batch
        if not obj:
            # Adding
            return (
                (None, {
                    'fields': ('project', 'name', 'assignments_per_task',
                               'allotted_assignment_time', 'csv_file'),
                }),
                ('Status', {
                    'fields': ('active',)
                }),
                ('Permissions', {
                    'fields': ('login_required', 'custom_permissions', 'worker_permissions')
                }),
            )
        else:
            # Changing
            return (
                (None, {
                    'fields': ('project', 'name', 'assignments_per_task',
                               'allotted_assignment_time', 'filename')
                }),
                ('Status', {
                    'fields': ('active', 'published')
                }),
                ('Permissions', {
                    'fields': ('login_required', 'custom_permissions', 'worker_permissions')
                }),
            )

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return []
        else:
            return ('assignments_per_task', 'filename', 'published')

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<int:batch_id>/cancel/',
                 self.admin_site.admin_view(self.cancel_batch), name='cancel_batch'),
            path('<int:batch_id>/review/',
                 self.admin_site.admin_view(self.review_batch), name='review_batch'),
            path('<int:batch_id>/publish/',
                 self.admin_site.admin_view(self.publish_batch), name='publish_batch'),
            path('<int:batch_id>/download/',
                 self.admin_site.admin_view(self.download_batch), name='download_batch'),
            path('<int:batch_id>/input/',
                 self.admin_site.admin_view(self.download_batch_input),
                 name='download_batch_input'),
            path('<int:batch_id>/stats/',
                 self.admin_site.admin_view(self.batch_stats), name='batch_stats'),
            path('update_csv_line_endings',
                 self.admin_site.admin_view(self.update_csv_line_endings),
                 name='update_csv_line_endings'),
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

        return redirect(reverse('turkle_admin:turkle_batch_changelist'))

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
        return redirect(reverse('turkle_admin:review_batch', kwargs={'batch_id': obj.id}))

    def response_change(self, request, obj):
        # catch unpublished batch when saved to redirect to review page
        if not obj.published:
            return redirect(reverse('turkle_admin:review_batch', kwargs={'batch_id': obj.id}))
        return super().response_change(request, obj)

    def review_batch(self, request, batch_id):
        request.current_app = self.admin_site.name
        try:
            batch = Batch.objects.get(id=batch_id)
        except ObjectDoesNotExist:
            messages.error(request, 'Cannot find Batch with ID {}'.format(batch_id))
            return redirect(reverse('turkle_admin:turkle_batch_changelist'))

        task_ids = list(batch.task_set.values_list('id', flat=True))
        task_ids_as_json = json.dumps(task_ids)
        return render(request, 'admin/turkle/review_batch.html', {
            'batch_id': batch_id,
            'first_task_id': task_ids[0],
            'task_ids_as_json': task_ids_as_json,
            'site_header': self.admin_site.site_header,
            'site_title': self.admin_site.site_title,
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

        if 'custom_permissions' in form.data:
            if 'worker_permissions' in form.data:
                existing_groups = set(get_groups_with_perms(obj))
                form_groups = set(form.cleaned_data['worker_permissions'])
                groups_to_add = form_groups.difference(existing_groups)
                groups_to_remove = existing_groups.difference(form_groups)
                for group in groups_to_add:
                    assign_perm('can_work_on_batch', group, obj)
                for group in groups_to_remove:
                    remove_perm('can_work_on_batch', group, obj)
            else:
                for group in get_groups_with_perms(obj):
                    remove_perm('can_work_on_batch', group, obj)

    def stats(self, obj):
        stats_url = reverse('turkle_admin:batch_stats', kwargs={'batch_id': obj.id})
        return format_html('<a href="{}" class="button">Stats</a>'.
                           format(stats_url))

    def update_csv_line_endings(self, request):
        csv_unix_line_endings = (request.POST['csv_unix_line_endings'] == 'true')
        request.session['csv_unix_line_endings'] = csv_unix_line_endings
        return JsonResponse({})


class ProjectForm(ModelForm):
    template_file_upload = FileField(label='HTML template file', required=False)
    worker_permissions = ModelMultipleChoiceField(
        label='Worker Groups with access to this Project',
        queryset=Group.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('Worker Groups', False),
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

        self.fields['assignments_per_task'].label = 'Assignments per Task'
        self.fields['assignments_per_task'].help_text = 'This parameter sets the default ' + \
            'number of Assignments per Task for new Batches of Tasks.  Changing this ' + \
            'parameter DOES NOT change the number of Assignments per Task for already ' + \
            'published batches of Tasks.'
        self.fields['custom_permissions'].label = 'Restrict access to specific Groups of Workers '
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

        initial_ids = [str(id)
                       for id in get_groups_with_perms(self.instance).values_list('id', flat=True)]
        self.fields['worker_permissions'].initial = initial_ids


class ProjectAdmin(GuardedModelAdmin):
    actions = [activate_projects, deactivate_projects]
    change_form_template = 'admin/turkle/project/change_form.html'
    form = ProjectForm
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '60'})},
    }
    list_display = ('name', 'filename', 'updated_at', 'active', 'stats', 'publish_tasks')
    list_filter = ('active', ProjectCreatorFilter)
    search_fields = ['name']

    # Fieldnames are extracted from form text, and should not be edited directly
    exclude = ('fieldnames',)
    readonly_fields = ('extracted_template_variables',)

    # required by django-admin-autocomplete-filter 0.5
    class Media:
        pass

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('autocomplete-order-by-name',
                 self.admin_site.admin_view(ProjectSearchView.as_view(model_admin=self)),
                 name='autocomplete_project_order_by_name'),
            path('<int:project_id>/stats/',
                 self.admin_site.admin_view(self.project_stats), name='project_stats'),
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
                    'fields': ('name', 'assignments_per_task')
                }),
                ('HTML Template', {
                    'fields': ('html_template', 'template_file_upload', 'filename')
                }),
                ('Status', {
                    'fields': ('active',)
                }),
                ('Default Permissions for new Batches', {
                    'fields': ('login_required', 'custom_permissions', 'worker_permissions')
                }),
            )
        else:
            # Changing
            return (
                (None, {
                    'fields': ('name', 'assignments_per_task')
                }),
                ('HTML Template', {
                    'fields': ('html_template', 'template_file_upload', 'filename',
                               'extracted_template_variables')
                }),
                ('Status', {
                    'fields': ('active',)
                }),
                ('Default Permissions for new Batches', {
                    'fields': ('login_required', 'custom_permissions', 'worker_permissions')
                }),
            )

    def project_stats(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except ObjectDoesNotExist:
            messages.error(request, 'Cannot find Project with ID {}'.format(project_id))
            return redirect(reverse('turkle_admin:turkle_project_changelist'))

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

        batch_ids = task_duration_by_batch.keys()
        stats_batches = []
        for batch in Batch.objects.filter(id__in=batch_ids).order_by('name'):
            has_completed_assignments = batch.id in task_duration_by_batch
            if has_completed_assignments:
                last_finished_time = task_updated_at_by_batch[batch.id][-1]
                mean_work_time = int(statistics.mean(task_duration_by_batch[batch.id]))
                median_work_time = int(statistics.median(task_duration_by_batch[batch.id]))
            else:
                last_finished_time = 'N/A'
                mean_work_time = 'N/A'
                median_work_time = 'N/A'
            assignments_completed = len(task_duration_by_batch[batch.id])
            total_task_assignments = batch.total_task_assignments()
            stats_batches.append({
                'batch_id': batch.id,
                'name': batch.name,
                'active': batch.active,
                'has_completed_assignments': has_completed_assignments,
                'assignments_completed': assignments_completed,
                'total_task_assignments': total_task_assignments,
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
            now = datetime.now(timezone.utc)
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

        return render(request, 'admin/turkle/project_stats.html', {
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

    def publish_tasks(self, instance):
        publish_tasks_url = '%s?project=%d&assignments_per_task=%d' % (
            reverse('turkle_admin:turkle_batch_add'),
            instance.id,
            instance.assignments_per_task)
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

        if 'custom_permissions' in form.data:
            if 'worker_permissions' in form.data:
                existing_groups = set(get_groups_with_perms(obj))
                form_groups = set(form.cleaned_data['worker_permissions'])
                groups_to_add = form_groups.difference(existing_groups)
                groups_to_remove = existing_groups.difference(form_groups)
                for group in groups_to_add:
                    assign_perm('can_work_on', group, obj)
                for group in groups_to_remove:
                    remove_perm('can_work_on', group, obj)
            else:
                for group in get_groups_with_perms(obj):
                    remove_perm('can_work_on', group, obj)

    def delete_model(self, request, obj):
        logger.info("User(%i) deleting Project(%i) %s", request.user.id, obj.id, obj.name)
        super().delete_model(request, obj)

    def stats(self, obj):
        stats_url = reverse('turkle_admin:project_stats', kwargs={'project_id': obj.id})
        return format_html('<a href="{}" class="button">Stats</a>'.
                           format(stats_url))


admin_site = TurkleAdminSite(name='turkle_admin')
admin_site.register(Group, CustomGroupAdmin)
admin_site.register(User, CustomUserAdmin)
admin_site.register(Batch, BatchAdmin)
admin_site.register(Project, ProjectAdmin)
