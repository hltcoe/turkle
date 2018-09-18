try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import random

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.conf import settings

from hits.models import Hit, HitBatch, HitTemplate


def download_batch_csv(request, batch_id):
    batch = HitBatch.objects.get(id=batch_id)
    csv_output = StringIO()
    batch.to_csv(csv_output)
    csv_string = csv_output.getvalue()
    response = HttpResponse(csv_string, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(
        batch.csv_results_filename())
    return response


def hits_list_context(template, more_map={}):
    c = dict(
        {
            'hit_templates': HitTemplate.objects.all()
        },
        **more_map
    )
    return template.render(c)


def index(request):
    t = loader.get_template('hits/index.html')
    return HttpResponse(hits_list_context(t))


def detail(request, hit_id):
    h = get_object_or_404(Hit, pk=hit_id)
    return render(
        request,
        'hits/detail.html',
        {'hit': h},
    )


def results(request, hit_id):
    return HttpResponse("You're looking at the results of hit %s." % hit_id)


def submission(request, hit_id):
    h = get_object_or_404(Hit, pk=hit_id)
    h.completed = True
    h.answers = dict(request.POST.items())
    h.save()

    if hasattr(settings, 'NEXT_HIT_ON_SUBMIT') and settings.NEXT_HIT_ON_SUBMIT:
        next_hit_random = hasattr(settings, 'RANDOM_NEXT_HIT_ON_SUBMIT') and \
                          settings.RANDOM_NEXT_HIT_ON_SUBMIT
        unfinished_hits = Hit.objects.filter(completed=False).order_by('id')
        try:
            next_hit = random.choice(unfinished_hits) if next_hit_random \
                else unfinished_hits[0]
            return redirect(detail, next_hit.id)
        except IndexError:
            pass

    t = loader.get_template('hits/submission.html')
    return HttpResponse(hits_list_context(t, {'submitted_hit': h}))
