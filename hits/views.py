from django.template import Context, loader
from hits.models import Hit
from django.http import HttpResponse

def index(request):
    latest_hit_list = Hit.objects.all().order_by('-id')[:5]
    t = loader.get_template('hits/index.html')
    c = Context({
        'latest_hit_list': latest_hit_list,
    })
    return HttpResponse(t.render(c))

def detail(request, hit_id):
    return HttpResponse("You're looking at hit %s." % hit_id)

def results(request, hit_id):
    return HttpResponse("You're looking at the results of hit %s." % hit_id)

def work_on(request, hit_id):
    return HttpResponse("You're working on hit %s." % hit_id)
