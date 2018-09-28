try:
    from cStringIO import StringIO
except ImportError:
    try:
        from StringIO import StringIO
    except ImportError:
        from io import BytesIO
        StringIO = BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from hits.models import Hit, HitAssignment, HitBatch, HitTemplate


def accept_hit(request, batch_id, hit_id):
    try:
        batch = HitBatch.objects.get(id=batch_id)
    except ObjectDoesNotExist:
        messages.error(request, u'Cannot find HIT Batch with ID {}'.format(batch_id))
        return redirect(index)
    try:
        hit = Hit.objects.get(id=hit_id)
    except ObjectDoesNotExist:
        messages.error(request, u'Cannot find HIT with ID {}'.format(hit_id))
        return redirect(index)

    try:
        with transaction.atomic():
            available_hits = batch.available_hits_for(request.user).select_for_update()
            available_hits.get(id=hit_id)  # Can raise ObjectDoesNotExist
            ha = HitAssignment()
            if request.user.is_authenticated:
                ha.assigned_to = request.user
            else:
                ha.assigned_to = None
            ha.hit = hit
            ha.save()
    except ObjectDoesNotExist:
        messages.error(request, u'The HIT with ID {} is no longer available'.format(hit_id))
        return redirect(index)

    return redirect(hit_assignment, hit.id, ha.id)


def accept_next_hit(request, batch_id):
    try:
        with transaction.atomic():
            batch = HitBatch.objects.get(id=batch_id)
            hit = batch.available_hits_for(request.user).select_for_update().first()
            if hit:
                ha = HitAssignment()
                if request.user.is_authenticated:
                    ha.assigned_to = request.user
                else:
                    ha.assigned_to = None
                ha.hit = hit
                ha.save()
    except ObjectDoesNotExist:
        messages.error(request, u'Cannot find HIT Batch with ID {}'.format(batch_id))
        return redirect(index)

    if hit:
        return redirect(hit_assignment, hit.id, ha.id)
    else:
        messages.error(request, u'No more HITs available from Batch {}'.format(batch_id))
        return redirect(index)


@staff_member_required
def download_batch_csv(request, batch_id):
    batch = HitBatch.objects.get(id=batch_id)
    csv_output = StringIO()
    batch.to_csv(csv_output)
    csv_string = csv_output.getvalue()
    response = HttpResponse(csv_string, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(
        batch.csv_results_filename())
    return response


def hit_assignment(request, hit_id, hit_assignment_id):
    try:
        hit = Hit.objects.get(id=hit_id)
    except ObjectDoesNotExist:
        messages.error(request, u'Cannot find HIT with ID {}'.format(hit_id))
        return redirect(index)
    try:
        hit_assignment = HitAssignment.objects.get(id=hit_assignment_id)
    except ObjectDoesNotExist:
        messages.error(request,
                       u'Cannot find HIT Assignment with ID {}'.format(hit_assignment_id))
        return redirect(index)

    if request.method == 'GET':
        return render(
            request,
            'hit_assignment.html',
            {
                'hit': hit,
                'hit_assignment': hit_assignment,
            },
        )
    else:
        hit_assignment.answers = dict(request.POST.items())
        hit_assignment.completed = True
        hit_assignment.save()

        if hasattr(settings, 'NEXT_HIT_ON_SUBMIT') and settings.NEXT_HIT_ON_SUBMIT:
            return redirect(accept_next_hit, hit.hit_batch.id)
        else:
            return redirect(index)


def hit_assignment_iframe(request, hit_id, hit_assignment_id):
    try:
        hit = Hit.objects.get(id=hit_id)
    except ObjectDoesNotExist:
        messages.error(request, u'Cannot find HIT with ID {}'.format(hit_id))
        return redirect(index)
    try:
        hit_assignment = HitAssignment.objects.get(id=hit_assignment_id)
    except ObjectDoesNotExist:
        messages.error(request,
                       u'Cannot find HIT Assignment with ID {}'.format(hit_assignment_id))
        return redirect(index)
    return render(
        request,
        'hit_assignment_iframe.html',
        {
            'hit': hit,
            'hit_assignment': hit_assignment,
        },
    )


def index(request):
    # Create a row for each Batch that has HITs available for the current user
    batch_rows = []
    for hit_template in HitTemplate.available_for(request.user):
        for hit_batch in hit_template.batches_available_for(request.user):
            total_hits_available = hit_batch.total_available_hits_for(request.user)
            if total_hits_available > 0:
                batch_rows.append({
                    'template_name': hit_template.name,
                    'batch_name': hit_batch.name,
                    'batch_published': hit_batch.date_published,
                    'assignments_available': total_hits_available,
                    'preview_next_hit_url': reverse('preview_next_hit',
                                                    kwargs={'batch_id': hit_batch.id}),
                    'accept_next_hit_url': reverse('accept_next_hit',
                                                   kwargs={'batch_id': hit_batch.id})
                })
    return render(request, 'index.html', {'batch_rows': batch_rows})


def preview(request, hit_id):
    try:
        hit = Hit.objects.get(id=hit_id)
    except ObjectDoesNotExist:
        messages.error(request, u'Cannot find HIT with ID {}'.format(hit_id))
        return redirect(index)
    return render(request, 'preview.html', {'hit': hit})


def preview_iframe(request, hit_id):
    try:
        hit = Hit.objects.get(id=hit_id)
    except ObjectDoesNotExist:
        messages.error(request, u'Cannot find HIT with ID {}'.format(hit_id))
        return redirect(index)
    return render(request, 'preview_iframe.html', {'hit': hit})


def preview_next_hit(request, batch_id):
    try:
        batch = HitBatch.objects.get(id=batch_id)
    except ObjectDoesNotExist:
        messages.error(request, u'Cannot find HIT Batch with ID {}'.format(batch_id))
        return redirect(index)
    hit = batch.next_available_hit_for(request.user)
    if hit:
        return redirect(preview, hit.id)
    else:
        messages.error(request,
                       u'No more HITs are available for Batch "{}"'.format(batch.name))
        return redirect(index)


def return_hit_assignment(request, hit_id, hit_assignment_id):
    try:
        hit = Hit.objects.get(id=hit_id)
    except ObjectDoesNotExist:
        messages.error(request, u'Cannot find HIT with ID {}'.format(hit_id))
        return redirect(index)
    try:
        hit_assignment = HitAssignment.objects.get(id=hit_assignment_id)
    except ObjectDoesNotExist:
        messages.error(request,
                       u'Cannot find HIT Assignment with ID {}'.format(hit_assignment_id))
        return redirect(index)

    if hit_assignment.completed:
        messages.error(request, u"The HIT can't be returned because it has been completed")
        return redirect(index)
    if request.user.is_authenticated:
        if hit_assignment.assigned_to != request.user:
            messages.error(request, u'The HIT you are trying to return belongs to another user')
            return redirect(index)
    else:
        if hit_assignment.assigned_to is not None:
            messages.error(request, u'The HIT you are trying to return belongs to another user')
            return redirect(index)

    hit_assignment.delete()
    return redirect(preview_next_hit, hit.hit_batch_id)
