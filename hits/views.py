try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from hits.models import Hit, HitAssignment, HitBatch, HitTemplate


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
        # TODO: Error handling
        pass


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
    return render(
        request,
        'hits/detail.html',
        {
            'hit': hit,
            'hit_assignment': hit_assignment,
        },
    )


def home(request):
    return render(request, 'index.html')


def index(request):
    return render(request, 'hits/index.html', {'batch_rows': _get_batch_table_rows(request)})


def detail(request, hit_id):
    h = get_object_or_404(Hit, pk=hit_id)
    return render(
        request,
        'hits/detail.html',
        {'hit': h},
    )


def submission(request, hit_id, hit_assignment_id):
    h = get_object_or_404(Hit, pk=hit_id)
    ha = get_object_or_404(HitAssignment, pk=hit_id)

    ha.answers = dict(request.POST.items())
    ha.completed = True
    ha.save()

    if hasattr(settings, 'NEXT_HIT_ON_SUBMIT') and settings.NEXT_HIT_ON_SUBMIT:
        return redirect(accept_next_hit, h.hit_batch.id)

    return render(request, 'hits/submission.html',
                  {
                      'batch_rows': _get_batch_table_rows(request),
                      'submitted_hit': h,
                  })


def _get_batch_table_rows(request):
    batch_rows = []
    for hit_template in HitTemplate.available_for(request.user):
        for hit_batch in hit_template.batches_available_for(request.user):
            batch_rows.append({
                'template_name': hit_template.name,
                'batch_name': hit_batch.name,
                'batch_published': hit_batch.date_published,
                'assignments_available': hit_batch.total_available_hits_for(request.user),
                'accept_next_hit_url': reverse('accept_next_hit',
                                               kwargs={'batch_id': hit_batch.id})
            })
    return batch_rows
