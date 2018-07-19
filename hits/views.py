from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.conf import settings
from hits.models import Hit, HitTemplate


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
        unfinished_hits = Hit.objects.filter(completed=False).order_by('id')
        try:
            return redirect(detail, unfinished_hits[0].id)
        except IndexError:
            pass

    t = loader.get_template('hits/submission.html')
    return HttpResponse(hits_list_context(t, {'submitted_hit': h}))
