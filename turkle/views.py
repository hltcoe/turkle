from django.http import HttpResponse
from django.template import Context, loader

def home(request):
    return HttpResponse(loader.get_template('index.html').render(Context({})))
