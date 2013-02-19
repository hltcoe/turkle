from django.core.urlresolvers import reverse
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, loader, RequestContext
from hits.models import Hit

def index(request):
    unfinished_hit_list = Hit.objects.filter(completed=False).order_by('-id')
    finished_hit_list = Hit.objects.filter(completed=True).order_by('-id')
    t = loader.get_template('hits/index.html')
    c = Context({
        'unfinished_hit_list': unfinished_hit_list,
        'finished_hit_list': finished_hit_list,
    })
    return HttpResponse(t.render(c))

def detail(request, hit_id):
    h = get_object_or_404(Hit, pk=hit_id)
    return render_to_response('hits/detail.html', {'hit': h},
                               context_instance=RequestContext(request))

def results(request, hit_id):
    return HttpResponse("You're looking at the results of hit %s." % hit_id)

def submission(request, hit_id):
    print(str(request.body))
    return HttpResponse("hola")
