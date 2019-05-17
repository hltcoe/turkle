from functools import wraps
from io import StringIO
import logging
import urllib

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.utils import OperationalError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.dateparse import parse_date

from turkle.models import Task, TaskAssignment, Batch, Project

logger = logging.getLogger(__name__)


def handle_db_lock(func):
    """Decorator that catches database lock errors from sqlite"""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except OperationalError as ex:
            # sqlite3 cannot handle concurrent transactions.
            # This should be very rare with just a few users.
            # If it happens often, switch to mysql or postgres.
            if str(ex) == 'database is locked':
                messages.error(request, u'The database is busy. Please try again.')
                return redirect(index)
            raise ex
    return wrapper


def index(request):
    """
    Security behavior:
    - Anyone can access the page, but the page only shows the user
      information they have access to.
    """
    abandoned_assignments = []
    if request.user.is_authenticated:
        for ha in TaskAssignment.objects.filter(assigned_to=request.user).filter(completed=False):
            abandoned_assignments.append({
                'task': ha.task,
                'task_assignment_id': ha.id
            })

    # Create a row for each Batch that has Tasks available for the current user
    batch_rows = []
    for project in Project.all_available_for(request.user):
        for batch in project.batches_available_for(request.user):
            total_tasks_available = batch.total_available_tasks_for(request.user)
            if total_tasks_available > 0:
                batch_rows.append({
                    'project_name': project.name,
                    'batch_name': batch.name,
                    'batch_published': batch.created_at,
                    'assignments_available': total_tasks_available,
                    'preview_next_task_url': reverse('preview_next_task',
                                                     kwargs={'batch_id': batch.id}),
                    'accept_next_task_url': reverse('accept_next_task',
                                                    kwargs={'batch_id': batch.id})
                })
    return render(request, 'index.html', {
        'abandoned_assignments': abandoned_assignments,
        'batch_rows': batch_rows
    })


@handle_db_lock
def accept_task(request, batch_id, task_id):
    """
    Accept task from preview

    Security behavior:
    - If the user does not have permission to access the Batch+Task, they
      are redirected to the index page with an error message.
    """
    try:
        batch = Batch.objects.get(id=batch_id)
    except ObjectDoesNotExist:
        messages.error(request, u'Cannot find Task Batch with ID {}'.format(batch_id))
        return redirect(index)
    try:
        task = Task.objects.get(id=task_id)
    except ObjectDoesNotExist:
        messages.error(request, u'Cannot find Task with ID {}'.format(task_id))
        return redirect(index)

    try:
        with transaction.atomic():
            # Lock access to the specified Task
            Task.objects.filter(id=task_id).select_for_update()

            # Will throw ObjectDoesNotExist exception if Task no longer available
            batch.available_tasks_for(request.user).get(id=task_id)

            ha = TaskAssignment()
            if request.user.is_authenticated:
                ha.assigned_to = request.user
            else:
                ha.assigned_to = None
            ha.task = task
            ha.save()
            if request.user.is_authenticated:
                logger.info('User(%i) accepted Task(%i)', request.user.id, task.id)
            else:
                logger.info('Anonymous user accepted Task(%i)', task.id)
    except ObjectDoesNotExist:
        messages.error(request, u'The Task with ID {} is no longer available'.format(task_id))
        return redirect(index)

    return redirect(task_assignment, task.id, ha.id)


@handle_db_lock
def accept_next_task(request, batch_id):
    """
    Accept task from index or auto accept next task

    Security behavior:
    - If the user does not have permission to access the Batch+Task, they
      are redirected to the index page with an error message.
    """
    try:
        with transaction.atomic():
            batch = Batch.objects.get(id=batch_id)

            # Lock access to all Tasks available to current user in the batch
            batch.available_task_ids_for(request.user).select_for_update()

            task_id = _skip_aware_next_available_task_id(request, batch)

            if task_id:
                ha = TaskAssignment()
                if request.user.is_authenticated:
                    ha.assigned_to = request.user
                else:
                    ha.assigned_to = None
                ha.task_id = task_id
                ha.save()
                if request.user.is_authenticated:
                    logger.info('User(%i) accepted Task(%i)', request.user.id, task_id)
                else:
                    logger.info('Anonymous user accepted Task(%i)', task_id)
    except ObjectDoesNotExist:
        messages.error(request, u'Cannot find Task Batch with ID {}'.format(batch_id))
        return redirect(index)

    if task_id:
        return redirect(task_assignment, task_id, ha.id)
    else:
        messages.error(request, u'No more Tasks available from Batch {}'.format(batch_id))
        return redirect(index)


@staff_member_required
def download_batch_csv(request, batch_id):
    """
    Security behavior:
    - Access to this page is limited to requesters.  Any requester can
      download any CSV file.
    """
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


@staff_member_required
def download_batch_input_csv(request, batch_id):
    """
    Security behavior:
    - Access to this page is limited to requesters.  Any requester can
      download any CSV file.
    """
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


def task_assignment(request, task_id, task_assignment_id):
    """
    Task view and submission (task content in iframe below)

    Security behavior:
    - If the user does not have permission to access the Task Assignment, they
      are redirected to the index page with an error message.
    """
    try:
        task = Task.objects.get(id=task_id)
    except ObjectDoesNotExist:
        messages.error(request, 'Cannot find Task with ID {}'.format(task_id))
        return redirect(index)
    try:
        task_assignment = TaskAssignment.objects.get(id=task_assignment_id)
    except ObjectDoesNotExist:
        messages.error(request,
                       'Cannot find Task Assignment with ID {}'.format(task_assignment_id))
        return redirect(index)

    if request.user.is_authenticated:
        if request.user != task_assignment.assigned_to:
            messages.error(
                request,
                'You do not have permission to work on the Task Assignment with ID {}'.
                format(task_assignment.id))
            return redirect(index)
    else:
        if task_assignment.assigned_to is not None:
            messages.error(
                request,
                'You do not have permission to work on the Task Assignment with ID {}'.
                format(task_assignment.id))
            return redirect(index)

    auto_accept_status = request.session.get('auto_accept_status', False)

    if request.method == 'GET':
        http_get_params = "?assignmentId={}&hitId={}&workerId={}&urlSubmitTo={}".format(
            task_assignment.id,
            task.id,
            request.user.id,
            urllib.parse.quote(
                reverse('task_assignment', kwargs={
                    'task_id': task.id, 'task_assignment_id': task_assignment.id}),
                safe=''))
        return render(
            request,
            'task_assignment.html',
            {
                'auto_accept_status': auto_accept_status,
                'http_get_params': http_get_params,
                'task': task,
                'task_assignment': task_assignment,
            },
        )
    else:
        task_assignment.answers = dict(request.POST.items())
        task_assignment.completed = True
        task_assignment.save()
        if request.user.is_authenticated:
            logger.info('User(%i) submitted Task(%i)', request.user.id, task.id)
        else:
            logger.info('Anonymous user submitted Task(%i)', task.id)

        if request.session.get('auto_accept_status'):
            return redirect(accept_next_task, task.batch.id)
        else:
            return redirect(index)


def task_assignment_iframe(request, task_id, task_assignment_id):
    """
    Task form served in an iframe

    Security behavior:
    - If the user does not have permission to access the Task Assignment, they
      are redirected to the index page with an error messge.
    """
    try:
        task = Task.objects.get(id=task_id)
    except ObjectDoesNotExist:
        messages.error(request, 'Cannot find Task with ID {}'.format(task_id))
        return redirect(index)
    try:
        task_assignment = TaskAssignment.objects.get(id=task_assignment_id)
    except ObjectDoesNotExist:
        messages.error(request,
                       'Cannot find Task Assignment with ID {}'.format(task_assignment_id))
        return redirect(index)

    if request.user.is_authenticated:
        if request.user != task_assignment.assigned_to:
            messages.error(
                request,
                'You do not have permission to work on the Task Assignment with ID {}'.
                format(task_assignment.id))
            return redirect(index)

    return render(
        request,
        'task_assignment_iframe.html',
        {
            'task': task,
            'task_assignment': task_assignment,
        },
    )


def preview(request, task_id):
    """
    Security behavior:
    - If the user does not have permission to access the Task, they
      are redirected to the index page with an error message.
    """
    try:
        task = Task.objects.get(id=task_id)
    except ObjectDoesNotExist:
        messages.error(request, 'Cannot find Task with ID {}'.format(task_id))
        return redirect(index)

    if not task.batch.project.available_for(request.user):
        messages.error(request, 'You do not have permission to view this Task')
        return redirect(index)

    http_get_params = "?assignmentId=ASSIGNMENT_ID_NOT_AVAILABLE&hitId={}".format(
        task.id)
    return render(request, 'preview.html', {
        'http_get_params': http_get_params,
        'task': task
    })


def preview_iframe(request, task_id):
    """
    Security behavior:
    - If the user does not have permission to access the Task, they
      are redirected to the index page with an error message.
    """
    try:
        task = Task.objects.get(id=task_id)
    except ObjectDoesNotExist:
        messages.error(request, 'Cannot find Task with ID {}'.format(task_id))
        return redirect(index)

    if not task.batch.project.available_for(request.user):
        messages.error(request, 'You do not have permission to view this Task')
        return redirect(index)

    return render(request, 'preview_iframe.html', {'task': task})


def preview_next_task(request, batch_id):
    """
    Security behavior:
    - If the user does not have permission to access the Batch, they
      are redirected to the index page with an error message.
    """
    try:
        batch = Batch.objects.get(id=batch_id)
    except ObjectDoesNotExist:
        messages.error(request, 'Cannot find Task Batch with ID {}'.format(batch_id))
        return redirect(index)

    task_id = _skip_aware_next_available_task_id(request, batch)

    if task_id:
        return redirect(preview, task_id)
    else:
        messages.error(request,
                       'No more Tasks are available for Batch "{}"'.format(batch.name))
        return redirect(index)


def return_task_assignment(request, task_id, task_assignment_id):
    """
    Security behavior:
    - If the user does not have permission to return the Assignment, they
      are redirected to the index page with an error message.
    """
    redirect_due_to_error = _delete_task_assignment(request, task_id, task_assignment_id)
    if redirect_due_to_error:
        return redirect_due_to_error
    if request.user.is_authenticated:
        logger.info('User(%i) returned Task(%i)', request.user.id, int(task_id))
    else:
        logger.info('Anonymous user returned Task(%i)', int(task_id))
    return redirect(index)


def skip_and_accept_next_task(request, batch_id, task_id, task_assignment_id):
    """
    Security behavior:
    - If the user does not have permission to return the Assignment, they
      are redirected to the index page with an error message.
    """
    redirect_due_to_error = _delete_task_assignment(request, task_id, task_assignment_id)
    if redirect_due_to_error:
        return redirect_due_to_error

    _add_task_id_to_skip_session(request.session, batch_id, task_id)
    if request.user.is_authenticated:
        logger.info('User(%i) skipped Task(%i)', request.user.id, int(task_id))
    else:
        logger.info('Anonymous user skipped Task(%i)', int(task_id))
    return redirect(accept_next_task, batch_id)


def skip_task(request, batch_id, task_id):
    """
    Skip to next task when previewing a task

    Security behavior:
    - This view updates a session variable that controls the order
      that Tasks are presented to a user.  Users cannot modify other
      users session variables.
    """
    _add_task_id_to_skip_session(request.session, batch_id, task_id)
    return redirect(preview_next_task, batch_id)


def stats(request):
    def format_seconds(s):
        """Converts seconds to string"""
        return '%dh %dm' % (s//3600, (s//60) % 60)

    if not request.user.is_authenticated:
        messages.error(
            request,
            u'You must be logged in to view the user statistics page')
        return redirect(index)

    try:
        start_date = parse_date(request.GET['start_date'])
    except MultiValueDictKeyError:
        start_date = None
    try:
        end_date = parse_date(request.GET['end_date'])
    except MultiValueDictKeyError:
        end_date = None

    tas = TaskAssignment.objects.filter(completed=True).filter(assigned_to=request.user)
    if start_date:
        tas = tas.filter(updated_at__gte=start_date)
    if end_date:
        tas = tas.filter(updated_at__lte=end_date)

    projects = Project.objects.filter(batch__task__taskassignment__assigned_to=request.user).\
        distinct()
    batches = Batch.objects.filter(task__taskassignment__assigned_to=request.user).distinct()

    elapsed_seconds_overall = 0
    project_stats = []
    for project in projects:
        project_batches = [b for b in batches if b.project_id == project.id]

        batch_stats = []
        elapsed_seconds_project = 0
        total_completed_project = 0
        for batch in project_batches:
            batch_tas = tas.filter(task__batch=batch)
            total_completed_batch = batch_tas.count()
            total_completed_project += total_completed_batch
            elapsed_seconds_batch = sum([ta.work_time_in_seconds() for ta in batch_tas])
            elapsed_seconds_project += elapsed_seconds_batch
            elapsed_seconds_overall += elapsed_seconds_batch
            if total_completed_batch > 0:
                batch_stats.append({
                    'batch_name': batch.name,
                    'elapsed_time_batch': format_seconds(elapsed_seconds_batch),
                    'total_completed_batch': total_completed_batch,
                })
        if total_completed_project > 0:
            project_stats.append({
                'project_name': project.name,
                'batch_stats': batch_stats,
                'elapsed_time_project': format_seconds(elapsed_seconds_project),
                'total_completed_project': total_completed_project,
            })

    if start_date:
        start_date = start_date.strftime('%Y-%m-%d')
    if end_date:
        end_date = end_date.strftime('%Y-%m-%d')

    return render(
        request,
        'stats.html',
        {
            'project_stats': project_stats,
            'end_date': end_date,
            'start_date': start_date,
            'total_completed': tas.count(),
            'total_elapsed_time': format_seconds(elapsed_seconds_overall),
        }
    )


def update_auto_accept(request):
    """
    Security behavior:
    - This view updates a session variable that controls whether or
      not Task Assignments are auto-accepted.  Users cannot modify other
      users session variables.
    """
    accept_status = (request.POST['auto_accept'] == 'true')
    request.session['auto_accept_status'] = accept_status
    return JsonResponse({})


def _add_task_id_to_skip_session(session, batch_id, task_id):
    """Add Task ID to session variable tracking Tasks the user has skipped
    """
    # The Django session store converts dictionary keys from ints to strings
    batch_id = str(batch_id)
    task_id = str(task_id)

    if 'skipped_tasks_in_batch' not in session:
        session['skipped_tasks_in_batch'] = {}
    if batch_id not in session['skipped_tasks_in_batch']:
        session['skipped_tasks_in_batch'][batch_id] = []
        session.modified = True
    if task_id not in session['skipped_tasks_in_batch'][batch_id]:
        session['skipped_tasks_in_batch'][batch_id].append(task_id)
        session.modified = True


@handle_db_lock
def _delete_task_assignment(request, task_id, task_assignment_id):
    """Delete a TaskAssignment, if possible

    Returns:
        - None if the TaskAssignment can be deleted, *OR*
        - An HTTPResponse object created by redirect() if there was an error

    Usage:
        redirect_due_to_error = _delete_task_assignment(request, task_id, task_assignment_id)
        if redirect_due_to_error:
            return redirect_due_to_error
    """
    try:
        task = Task.objects.get(id=task_id)
    except ObjectDoesNotExist:
        messages.error(request, 'Cannot find Task with ID {}'.format(task_id))
        return redirect(index)
    try:
        task_assignment = TaskAssignment.objects.get(id=task_assignment_id)
    except ObjectDoesNotExist:
        messages.error(request,
                       'Cannot find Task Assignment with ID {}'.format(task_assignment_id))
        return redirect(index)

    if task_assignment.completed:
        messages.error(request, u"The Task can't be returned because it has been completed")
        return redirect(index)
    if request.user.is_authenticated:
        if task_assignment.assigned_to != request.user:
            messages.error(request, 'The Task you are trying to return belongs to another user')
            return redirect(index)
    else:
        if task_assignment.assigned_to is not None:
            messages.error(request, 'The Task you are trying to return belongs to another user')
            return redirect(index)
        if task.batch.project.login_required:
            messages.error(request, 'You do not have permission to access this Task')
            return redirect(index)

    with transaction.atomic():
        # Lock access to the specified Task
        Task.objects.filter(id=task_id).select_for_update()

        task_assignment.delete()


def _skip_aware_next_available_task_id(request, batch):
    """Get next available Task for user, taking into account previously skipped Tasks

    This function will first look for an available Task that the user
    has not previously skipped.  If the only available Tasks are Tasks
    that the user has skipped, this function will return the first
    such Task.

    Returns:
        Task ID (int), or None if no more Tasks are available
    """
    def _get_skipped_task_ids_for_batch(session, batch_id):
        batch_id = str(batch_id)
        if 'skipped_tasks_in_batch' in session and \
           batch_id in session['skipped_tasks_in_batch']:
            return session['skipped_tasks_in_batch'][batch_id]
        else:
            return None

    available_task_ids = batch.available_task_ids_for(request.user)
    skipped_ids = _get_skipped_task_ids_for_batch(request.session, batch.id)

    if skipped_ids:
        task_id = available_task_ids.exclude(id__in=skipped_ids).first()
        if not task_id:
            task_id = available_task_ids.filter(id__in=skipped_ids).first()
            if task_id:
                messages.info(request, 'Only previously skipped Tasks are available')

                # Once all remaining Tasks have been marked as skipped, we clear
                # their skipped status.  If we don't take this step, then a Task
                # cannot be skipped a second time.
                request.session['skipped_tasks_in_batch'][str(batch.id)] = []
                request.session.modified = True
    else:
        task_id = available_task_ids.first()

    return task_id
