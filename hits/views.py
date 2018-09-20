try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import random

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

from hits.models import Hit, HitAssignment, HitBatch, HitTemplate


def claim_hit(request, hit_id):
    hit = get_object_or_404(Hit, pk=hit_id)
    # TODO: Verify that current user can claim HIT
    ha = HitAssignment()
    ha.assigned_to = request.user
    ha.hit = hit
    ha.save()
    return redirect(hit_assignment, hit_id, ha.id)


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
    return render(request, 'hits/index.html', {'hit_templates': HitTemplate.objects.all()})


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
        next_hit_random = hasattr(settings, 'RANDOM_NEXT_HIT_ON_SUBMIT') and \
                          settings.RANDOM_NEXT_HIT_ON_SUBMIT
        unfinished_hits = Hit.objects.filter(completed=False).order_by('id')
        try:
            next_hit = random.choice(unfinished_hits) if next_hit_random \
                else unfinished_hits[0]
            return redirect(claim_hit, next_hit.id)
        except IndexError:
            pass

    return render(request, 'hits/submission.html',
                  {
                      'submitted_hit': h,
                      'hit_templates': HitTemplate.objects.all(),
                  })
