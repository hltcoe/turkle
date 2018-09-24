try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from hits.models import Hit, HitAssignment, HitBatch, HitTemplate


def accept_hit(request, batch_id, hit_id):
    batch = get_object_or_404(HitBatch, pk=batch_id)
    hit = get_object_or_404(Hit, pk=hit_id)

    try:
        batch.available_hits_for(request.user).get(id=hit_id)
    except ObjectDoesNotExist:
        # TODO: Pass error message for user on to index view
        redirect(index)

    # TODO: Handle possible race condition for two users claiming assignment
    ha = HitAssignment()
    ha.assigned_to = request.user
    ha.hit = hit
    ha.save()
    return redirect(hit_assignment, hit.id, ha.id)


def accept_next_hit(request, batch_id):
    batch = get_object_or_404(HitBatch, pk=batch_id)
    hit = batch.next_available_hit_for(request.user)
    # TODO: Handle possible race condition for two users claiming assignment
    if hit:
        ha = HitAssignment()
        ha.assigned_to = request.user
        ha.hit = hit
        ha.save()
        return redirect(hit_assignment, hit.id, ha.id)
    else:
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
    hit = get_object_or_404(Hit, pk=hit_id)
    hit_assignment = get_object_or_404(HitAssignment, pk=hit_assignment_id)

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
    hit = get_object_or_404(Hit, pk=hit_id)
    hit_assignment = get_object_or_404(HitAssignment, pk=hit_assignment_id)
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
    hit = get_object_or_404(Hit, pk=hit_id)
    return render(request, 'preview.html', {'hit': hit})


def preview_iframe(request, hit_id):
    hit = get_object_or_404(Hit, pk=hit_id)
    return render(request, 'preview_iframe.html', {'hit': hit})


def preview_next_hit(request, batch_id):
    batch = get_object_or_404(HitBatch, pk=batch_id)
    hit = batch.next_available_hit_for(request.user)
    return redirect(preview, hit.id)
